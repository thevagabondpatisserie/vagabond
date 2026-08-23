// APPVER = '75'. TU BAN NAY MA APP THAT NAM TRONG REPO GITHUB:
//   thevagabondpatisserie/vagabond -> vagabond/public/js/app_bep.js
// Muon sua app: sua file do tren GitHub, deploy bench roi cap nhat site.
// Web Page nay chi con doan nap file duoi day, DUNG dan nguyen ma app tro lai day.
// Server Script 'Chan ghi de APPVER - Web Page' van bao ve doan nap nay.
(function () {
  var s = document.createElement('script');
  s.src = '/assets/vagabond/js/app_bep.js?t=' + (new Date()).getTime();
  document.body.appendChild(s);
})();