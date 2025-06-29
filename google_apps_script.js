// Google Apps Script để gửi webhook khi có form response mới
// Code thực tế hiện tại của user

function sendBookingToWebhook() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Form1");

  if (!sheet) {
    Logger.log("Sheet không tồn tại, kiểm tra lại tên Sheet.");
    return;
  }

  var lastRow = sheet.getLastRow();
  if (lastRow === 0) {
    Logger.log("Sheet trống, không có dữ liệu.");
    return;
  }

  var data = sheet.getRange(lastRow, 1, 1, sheet.getLastColumn()).getValues()[0];
  Logger.log("Raw data from sheet: " + JSON.stringify(data));

  var name = data[1] || "Không có thông tin";
  var phone = data[2] || "Không có số điện thoại";
  var customerCount = data[3] || "Không có khách hàng";
  var room = data[4] || "Chưa chọn";
  var date = data[5] || "Không có ngày";
  var startTime = data[6]; // Gửi dữ liệu thô
  var endTime = data[7];   // Gửi dữ liệu thô
  var notes = data[8] || "Không có ghi chú";
  var email = data[9] || "";

  Logger.log("startTime raw: " + startTime + " (type: " + typeof startTime + ")");
  Logger.log("endTime raw: " + endTime + " (type: " + typeof endTime + ")");

  // Đóng gói payload gửi về Flask (Python server)
  // Format thời gian để tránh bị convert UTC khi JSON.stringify()
  var payload = {
    "name": name,
    "phone": phone,
    "customerCount": customerCount,
    "room": room,
    "date": formatDate(date),
    "startTime": startTime.getHours() + ":" + (startTime.getMinutes() < 10 ? '0' + startTime.getMinutes() : startTime.getMinutes()),
    "endTime": endTime.getHours() + ":" + (endTime.getMinutes() < 10 ? '0' + endTime.getMinutes() : endTime.getMinutes()),
    "notes": notes,
    "email": email,
    "rowNumber": lastRow
  };

  Logger.log("Final payload: " + JSON.stringify(payload));

  var url = "https://09bf-115-76-117-120.ngrok-free.app/webhook/booking";

  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };

  try {
    var response = UrlFetchApp.fetch(url, options);
    Logger.log(response.getContentText());
    
    // Set trạng thái ban đầu sau khi gửi webhook thành công
    setInitialBookingStatus(lastRow);
    
  } catch (err) {
    Logger.log("Lỗi gửi webhook: " + err);
  }
}

function formatDate(dateValue) {
  if (!dateValue) return "Chưa chọn ngày";
  var date = new Date(dateValue);
  var day = date.getDate();
  var month = date.getMonth() + 1;
  var year = date.getFullYear();
  return `${day}/${month}/${year}`
}

// Thêm hàm để set trạng thái ban đầu cho booking mới
function setInitialBookingStatus(rowNumber) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Form1");
    if (!sheet) {
      Logger.log("Sheet không tồn tại");
      return;
    }
    
    // Set trạng thái ban đầu là "Chờ xử lý" (cột K)
    sheet.getRange(rowNumber, 11).setValue("Chờ xử lý");
    Logger.log("Set initial status 'Chờ xử lý' for row " + rowNumber);
    
  } catch (error) {
    Logger.log("Error setting initial status: " + error);
  }
}
