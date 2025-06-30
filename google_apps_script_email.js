/**
 * Google Apps Script Web App để nhận email requests từ Python server
 * Deploy script này dưới dạng Web App với quyền "Execute as: Me" và "Who has access: Anyone"
 */

/**
 * Hàm chính xử lý POST requests từ Python server
 */
function doPost(e) {
  try {
    // Parse request body
    const requestBody = JSON.parse(e.postData.contents);
    
    // Log request để debug
    console.log('Received email request:', requestBody);
    
    // Validate required fields
    if (!requestBody.to || !requestBody.subject || !requestBody.body) {
      return ContentService
        .createTextOutput(JSON.stringify({
          success: false,
          error: 'Missing required fields: to, subject, body'
        }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // Check if this is a test request
    if (requestBody.test === true) {
      console.log('Test request received, not sending actual email');
      return ContentService
        .createTextOutput(JSON.stringify({
          success: true,
          message: 'Test request successful - Apps Script is working'
        }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // Extract email parameters
    const to = requestBody.to;
    const subject = requestBody.subject;
    const body = requestBody.body;
    const htmlBody = requestBody.htmlBody || null;
    const senderName = requestBody.senderName || 'Discord Booking System';
    
    // Send email using MailApp
    const emailOptions = {
      name: senderName
    };
    
    if (htmlBody) {
      emailOptions.htmlBody = htmlBody;
    }
    
    // Send the email
    MailApp.sendEmail(to, subject, body, emailOptions);
    
    console.log(`Email sent successfully to ${to}`);
    
    // Return success response
    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: `Email sent successfully to ${to}`,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    console.error('Error sending email:', error);
    
    // Return error response
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        error: error.toString(),
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Hàm xử lý GET requests (optional - để test)
 */
function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({
      status: 'active',
      service: 'Discord Booking Email Service',
      timestamp: new Date().toISOString(),
      message: 'Email service is running. Use POST to send emails.'
    }))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Hàm test để gửi email thử nghiệm
 */
function testSendEmail() {
  const testData = {
    to: 'test@example.com',
    subject: 'Test Email from Apps Script',
    body: 'This is a test email sent from Google Apps Script.',
    htmlBody: '<h1>Test Email</h1><p>This is a <strong>test email</strong> sent from Google Apps Script.</p>',
    senderName: 'Discord Booking System Test'
  };
  
  try {
    MailApp.sendEmail(
      testData.to, 
      testData.subject, 
      testData.body,
      {
        name: testData.senderName,
        htmlBody: testData.htmlBody
      }
    );
    
    console.log('Test email sent successfully');
    return 'Test email sent successfully';
    
  } catch (error) {
    console.error('Test email failed:', error);
    return 'Test email failed: ' + error.toString();
  }
}

/**
 * Hàm setup permissions (chạy một lần để cấp quyền)
 */
function setupPermissions() {
  // Chạy hàm này một lần để cấp quyền MailApp
  try {
    MailApp.getRemainingDailyQuota();
    console.log('Permissions setup successful');
    return 'Permissions setup successful';
  } catch (error) {
    console.error('Permissions setup failed:', error);
    return 'Permissions setup failed: ' + error.toString();
  }
}
