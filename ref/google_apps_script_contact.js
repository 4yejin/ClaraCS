function doPost(e) {
  try {
    // e 파라미터 확인
    if (!e) {
      Logger.log('Error: e parameter is undefined');
      var output = ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: '요청 파라미터가 없습니다.'
      }));
      output.setMimeType(ContentService.MimeType.JSON);
      return output;
    }
    
    // e.parameter 확인
    if (!e.parameter) {
      Logger.log('Error: e.parameter is undefined');
      Logger.log('e.postData: ' + (e.postData ? 'exists' : 'undefined'));
      
      // e.postData에서 데이터 추출 시도 (JSON 형식인 경우)
      if (e.postData && e.postData.contents) {
        try {
          var postData = JSON.parse(e.postData.contents);
          var name = postData.name;
          var email = postData.email;
          var message = postData.message;
          
          Logger.log('Received data from postData - name: ' + name + ', email: ' + email + ', message: ' + message);
        } catch (parseError) {
          Logger.log('Error parsing postData: ' + parseError.toString());
          var output = ContentService.createTextOutput(JSON.stringify({
            success: false,
            error: '데이터 파싱 오류: ' + parseError.toString()
          }));
          output.setMimeType(ContentService.MimeType.JSON);
          return output;
        }
      } else {
        var output = ContentService.createTextOutput(JSON.stringify({
          success: false,
          error: '요청 데이터를 찾을 수 없습니다.'
        }));
        output.setMimeType(ContentService.MimeType.JSON);
        return output;
      }
    } else {
      // 정상적인 경우: e.parameter에서 데이터 추출
      var name = e.parameter.name;
      var email = e.parameter.email;
      var message = e.parameter.message;
      
      Logger.log('Received data from parameter - name: ' + name + ', email: ' + email + ', message: ' + message);
    }
    
    // 데이터 유효성 검사 (name, email, message는 위에서 정의됨)
    
    // 필수 필드 확인
    if (!name || !email || !message) {
      Logger.log('Missing required fields');
      var output = ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: '필수 필드가 누락되었습니다.'
      }));
      output.setMimeType(ContentService.MimeType.JSON);
      return output;
    }
    
    // 스프레드시트 접근
    var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    if (!spreadsheet) {
      Logger.log('Spreadsheet access failed');
      var output = ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: '스프레드시트에 접근할 수 없습니다.'
      }));
      output.setMimeType(ContentService.MimeType.JSON);
      return output;
    }
    
    // 시트 접근 - 한글 시트 이름 "시트1" 사용
    var sheet = spreadsheet.getSheetByName("시트1");
    if (!sheet) {
      // 사용 가능한 시트 이름 로깅
      var availableSheets = spreadsheet.getSheets().map(function(s) { return s.getName(); }).join(', ');
      Logger.log('Sheet "시트1" not found. Available sheets: ' + availableSheets);
      
      // 시트1이 없으면 첫 번째 시트 사용
      var sheets = spreadsheet.getSheets();
      if (sheets.length > 0) {
        sheet = sheets[0];
        Logger.log('Using first available sheet: ' + sheet.getName());
      } else {
        var output = ContentService.createTextOutput(JSON.stringify({
          success: false,
          error: '시트를 찾을 수 없습니다.'
        }));
        output.setMimeType(ContentService.MimeType.JSON);
        return output;
      }
    } else {
      Logger.log('Sheet "시트1" found successfully');
    }
    
    // 데이터 추가
    sheet.appendRow([name, email, message, new Date()]);
    Logger.log('Data appended successfully');
    
    // 성공 응답 (setHeaders 제거 - 서버 간 통신에서는 불필요)
    var output = ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: 'Success'
    }));
    output.setMimeType(ContentService.MimeType.JSON);
    return output;
      
  } catch (error) {
    // 에러 처리
    Logger.log('Error: ' + error.toString());
    Logger.log('Error stack: ' + error.stack);
    
    var output = ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString()
    }));
    output.setMimeType(ContentService.MimeType.JSON);
    return output;
  }
}

