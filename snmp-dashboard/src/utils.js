// src/utils.js

/**
 * Checks a value against warning and critical thresholds.
 * @param {number} value The metric's value
 * @param {object} thresholds An object like { warn: 70, crit: 90 }
 * @returns {string} 'good', 'warning', or 'critical'
 */
export function getMetricStatus(value, thresholds) {
  if (value > thresholds.crit) {
    return 'critical'; // Red
  }
  if (value > thresholds.warn) {
    return 'warning'; // Yellow
  }
  return 'good'; // Green
}


// src/utils.js (Add this function to the bottom of the file)
// Commented out: Duplicate function from deviceService.js
// export function getCookie(name) {
//     let cookieValue = null;
//     if (document.cookie && document.cookie !== '') {
//         const cookies = document.cookie.split(';');
//         for (let i = 0; i < cookies.length; i++) {
//             let cookie = cookies[i].trim();
//             // Does this cookie string begin with the name we want?
//             if (cookie.substring(0, name.length + 1) === (name + '=')) {
//                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                 break;
//             }
//         }
//     }
//     return cookieValue;
// }