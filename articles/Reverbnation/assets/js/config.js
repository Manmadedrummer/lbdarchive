/* ==========================================================================
   SITE SETTINGS  (edit this file)
   ==========================================================================
   AUDIO — where each song plays from. Three ways to set it up, use ONE:

   1) archive.org item (easiest): put the item's identifier below, e.g. if your
      page is  https://archive.org/details/lethal-by-default-ep  then
      archiveItem = "lethal-by-default-ep".  The mp3 file names inside the item
      must match the names in archiveFiles (change them if yours differ).

   2) Per-song full URLs: fill in `audio` below, e.g.
        "who-am-i": "https://archive.org/download/lethal-by-default-ep/05_Who_Am_I_.mp3"

   3) Local files: leave everything empty and drop the mp3s in the /audio folder
      using the default names listed in archiveFiles.
   ========================================================================== */
window.RN_CONFIG = {
  archiveItem: "LBD-The-Broadcast",     // archive.org item: https://archive.org/details/LBD-The-Broadcast
  archiveFiles: {
    "man-in-the-moon":      "02 Man In The Moon.mp3",
    "the-homeless-must-go": "04 The Homeless Must Go.mp3",
    "who-am-i":             "05 Who Am I.mp3"
  },
  audio: {
    // "man-in-the-moon": "https://archive.org/download/.../02_Man_In_The_Moon.mp3",
    // "the-homeless-must-go": "",
    // "who-am-i": ""
  },
  // OPTIONAL: local video files by YouTube id, e.g. "DL2T2cds4Hk": "video/skys-the-limit.mp4"
  video: {}
};
