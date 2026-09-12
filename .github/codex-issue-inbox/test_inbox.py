import copy
import io
import contextlib
import http.client
import datetime as dt
import unittest
from inbox import command, reconcile, receipt, sweep, PREFIX

NOW = dt.datetime(2026, 9, 11, tzinfo=dt.timezone.utc)
USER = {'login': 'owner', 'type': 'User'}

def item(i, body, user=USER):
    return {'id': i, 'created_at': NOW.isoformat(), 'body': body, 'user': user, 'html_url': f'https://github.com/o/r/issues/1#issuecomment-{i}'}

class API:
    def __init__(self, comments=None):
        self.comments = comments or []
        self.labels = []
        self.fail_after_post = False
        self.label_calls = []
    def pages(self, path):
        return copy.deepcopy(self.comments)
    def allowed(self, user):
        return user == USER
    def request(self, method, path, data=None):
        if path.endswith('/comments'):
            self.comments.append(item(1000+len(self.comments), data['body'], {'login':'github-actions[bot]', 'type':'Bot'}))
            if self.fail_after_post:
                self.fail_after_post = False
                raise TimeoutError('response lost after commit')
        else:
            self.label_calls.append((method, path))
            self.labels = data['labels'] if method == 'POST' else []

class InboxTests(unittest.TestCase):
    def setUp(self):
        self.issue = {**item(1, 'Task\n\n@codex review'), 'number': 1, 'state': 'open'}
    def run_inbox(self, api):
        return reconcile(api, self.issue, NOW, 'https://github.com/o/r/actions/runs/1')
    def test_issue_body_received_without_comment(self):
        api=API();self.assertEqual(self.run_inbox(api),1)
        self.assertEqual(receipt(api.comments[0])['status'],'queued')
    def test_repeated_event_and_edited_body_do_not_repeat(self):
        api=API();self.run_inbox(api);self.issue['body']='@codex changed'
        self.assertEqual(self.run_inbox(api),0);self.assertEqual(len(api.comments),1)
    def test_lost_response_reconciles_without_duplicate(self):
        api=API();api.fail_after_post=True
        with self.assertRaises(TimeoutError):self.run_inbox(api)
        self.assertEqual(self.run_inbox(api),0);self.assertEqual(len(api.comments),1)
        self.assertEqual(api.labels,['codex:queued'])
    def test_three_accepted_then_explicit_limit(self):
        api=API([item(i,'@codex task') for i in range(2,6)])
        self.assertEqual(self.run_inbox(api),3)
        states=[receipt(c)['status'] for c in api.comments if receipt(c)]
        self.assertEqual(states,['queued']*3+['limited']*2)
        self.assertEqual(self.run_inbox(api),0)
    def test_new_request_after_24h(self):
        api=API();self.run_inbox(api)
        api.comments += [item(2,'@codex task')]
        self.assertEqual(reconcile(api,self.issue,NOW+dt.timedelta(hours=25),'url'),1)
    def test_bot_and_outside_collaborator_cannot_call(self):
        for user in [{'login':'claude[bot]','type':'Bot'},{'login':'stranger','type':'User'}]:
            self.issue['user']=user;self.assertEqual(self.run_inbox(API()),0)
    def test_pr_and_closed_issue_ignored(self):
        self.issue['pull_request']={'url':'x'};self.assertEqual(self.run_inbox(API()),0)
        del self.issue['pull_request'];self.issue['state']='closed';self.assertEqual(self.run_inbox(API()),0)
    def test_quotes_code_and_other_names_ignored(self):
        for body in ['> @codex review','```\n@codex review\n```','~~~\n@codex review\n~~~','    @codex review','example @codex review','@codexfoo hi','<!--\n@codex review\n-->']:
            self.assertIsNone(command(body),body)
    def test_user_cannot_forge_receipt(self):
        api=API();self.run_inbox(api)
        forged=copy.deepcopy(api.comments[0]);forged['user']=USER
        api=API([forged]);self.assertEqual(self.run_inbox(api),1)
    def test_old_requests_are_not_replayed_on_install(self):
        api=API()
        self.assertEqual(reconcile(api,self.issue,NOW,'url',NOW+dt.timedelta(seconds=1)),0)
    def test_malformed_bot_receipt_is_not_trusted(self):
        api=API();self.run_inbox(api)
        api.comments[0]['body']=api.comments[0]['body'].replace(NOW.isoformat(),'bad-date')
        self.assertIsNone(receipt(api.comments[0]))
    def test_event_sweep_recovers_multiple_comments(self):
        api=API([item(2,'@codex first'),item(3,'@codex second')])
        self.assertEqual(self.run_inbox(api),3)
    def test_deleted_user_does_not_block_other_requests(self):
        api=API([item(2,'@codex task',None),item(3,'@codex valid')])
        self.assertEqual(self.run_inbox(api),2)
        self.assertIsNone(receipt(item(9,'bad',None)))
    def test_existing_queue_label_is_not_posted_again(self):
        api=API();self.run_inbox(api)
        self.issue['labels']=[{'name':'codex:queued'}]
        self.run_inbox(api)
        self.assertEqual(len(api.label_calls),1)
    def test_completed_queue_removes_only_queue_label(self):
        api=API();self.run_inbox(api)
        api.comments[0]['body']=api.comments[0]['body'].replace('"queued"','"done"')
        self.issue['labels']=[{'name':'codex:queued'},{'name':'other'}]
        self.run_inbox(api)
        self.assertEqual(api.label_calls[-1],('DELETE','/issues/1/labels/codex:queued'))
    def test_failed_issue_does_not_starve_next_issue(self):
        class Broken(API):
            def pages(self,path):
                if path == '/issues/1/comments':raise OSError('network')
                return super().pages(path)
        api=Broken()
        second={**self.issue,'number':2,'id':2}
        with self.assertRaisesRegex(RuntimeError,'#1: OSError'):
            sweep(api,[self.issue,second],NOW,'url',None)
        self.assertEqual(len(api.comments),1)
        self.assertEqual(receipt(api.comments[0])['source'],'issue:2')

    def test_incomplete_read_keeps_next_issue_and_diagnostic_without_payload(self):
        class Broken(API):
            def pages(self,path):
                if path == '/issues/1/comments':
                    raise http.client.IncompleteRead(b'PRIVATE_PAYLOAD', 100)
                return super().pages(path)
        api=Broken(); log=io.StringIO()
        with contextlib.redirect_stderr(log):
            with self.assertRaisesRegex(RuntimeError, '#1: IncompleteRead'):
                sweep(api,[self.issue,{**self.issue,'number':2,'id':2}],NOW,'url',None)
        self.assertEqual(receipt(api.comments[0])['source'],'issue:2')
        self.assertIn('Issue #1: IncompleteRead',log.getvalue())
        self.assertIn('trong pages',log.getvalue())
        self.assertIn('test_inbox.py:',log.getvalue())
        self.assertNotIn('PRIVATE_PAYLOAD',log.getvalue())

    def test_operator_interrupt_is_not_swallowed(self):
        class Interrupted(API):
            def pages(self,path): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            sweep(Interrupted(),[self.issue],NOW,'url',None)

if __name__ == '__main__':unittest.main()
