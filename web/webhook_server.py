from flask import Flask, request, jsonify
import logging
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def create_app(discord_bot=None):
    """
    Tạo Flask app có webhook endpoints cho booking Discord.
    """
    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'Discord Booking System'
        })

    @app.route('/webhook/booking', methods=['POST'])
    def webhook_booking():
        """
        Nhận webhook booking từ Google Apps Script.
        """
        try:
            # Kiểm tra content-type
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400

            data = request.get_json()
            logger.info(f"Received booking: {json.dumps(data, ensure_ascii=False)}")

            # Validate field bắt buộc
            required_fields = ['email', 'name', 'date', 'startTime', 'endTime', 'room']
            missing_fields = [f for f in required_fields if not data.get(f)]
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

            # Chuẩn hóa dữ liệu
            def parse_time(time_str):
                """Parse time từ Google Sheets - xử lý nhiều format khác nhau"""
                try:
                    logger.info(f"Parsing time: {time_str} (type: {type(time_str)})")
                    
                    # Nếu là None hoặc empty
                    if not time_str:
                        logger.warning("Time is None or empty")
                        return ""
                    
                    # Convert to string
                    time_str = str(time_str).strip()
                    
                    # Format 1: Plain time string (21:00) - Format mới từ Apps Script
                    if ':' in time_str and not 'T' in time_str:
                        import re
                        match = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', time_str)
                        if match:
                            hours = int(match.group(1))
                            minutes = int(match.group(2))
                            result = f"{hours:02d}:{minutes:02d}"
                            logger.info(f"Plain time format parsed: {result}")
                            return result
                    
                    # Format 2: ISO format từ Google Sheets (1899-12-30T21:00:00.000Z) - Format cũ
                    if 'T' in time_str:
                        from datetime import timedelta
                        if 'Z' in time_str:
                            time_str = time_str.replace('Z', '')
                        if '.' in time_str:
                            # Có milliseconds: 1899-12-30T21:00:00.000
                            dt = datetime.fromisoformat(time_str)
                        else:
                            # Không có milliseconds: 1899-12-30T21:00:00
                            dt = datetime.fromisoformat(time_str)
                        
                        # Google Sheets gửi UTC time, cần convert về VN time
                        # Thử +8 tiếng thay vì +7 (có thể do daylight saving hoặc base time khác)
                        vn_time = dt + timedelta(hours=8)
                        result = vn_time.strftime('%H:%M')
                        logger.info(f"ISO format parsed (with +8h): {result}")
                        return result
                    
                    # Format 3: Số decimal từ Google Sheets (0.875 = 21:00)
                    try:
                        time_float = float(time_str)
                        if 0 <= time_float <= 1:
                            # Decimal time (0.875 = 21 giờ)
                            total_minutes = int(time_float * 24 * 60)
                            hours = total_minutes // 60
                            minutes = total_minutes % 60
                            result = f"{hours:02d}:{minutes:02d}"
                            logger.info(f"Decimal time format parsed: {result}")
                            return result
                    except ValueError:
                        pass
                    
                    # Nếu không match format nào, trả về original
                    logger.warning(f"No format matched for time: {time_str}")
                    return str(time_str)
                    
                except Exception as e:
                    logger.error(f"Error parsing time {time_str}: {e}")
                    return str(time_str)
            
            def normalize_date(date_str):
                """Normalize date format from d/m/yyyy to dd/mm/yyyy"""
                try:
                    date_str = str(date_str).strip()
                    # Kiểm tra format d/m/yyyy hoặc dd/mm/yyyy
                    import re
                    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
                    if match:
                        day = int(match.group(1))
                        month = int(match.group(2))
                        year = int(match.group(3))
                        result = f"{day:02d}/{month:02d}/{year}"
                        logger.info(f"Date normalized: {date_str} → {result}")
                        return result
                    return date_str
                except Exception as e:
                    logger.error(f"Error normalizing date {date_str}: {e}")
                    return str(date_str)
            
            booking_data = {
                'email': str(data.get('email', '')).strip(),
                'name': str(data.get('name', '')).strip(),
                'phone': str(data.get('phone', '')).strip(),
                'customerCount': str(data.get('customerCount', 1)).strip(),
                'date': normalize_date(data.get('date', '')),
                'startTime': parse_time(data.get('startTime', '')),
                'endTime': parse_time(data.get('endTime', '')),
                'room': str(data.get('room', '')).strip(),
                'notes': str(data.get('notes', '')).strip(),
                'rowNumber': data.get('rowNumber', 0)
            }

            # Validate email format
            email = booking_data['email']
            if '@' not in email or '.' not in email:
                return jsonify({'error': 'Invalid email format'}), 400

            # Check conflict sử dụng GoogleSheetsManager
            try:
                from google_sheets.manager import GoogleSheetsManager
                sheets_manager = GoogleSheetsManager()
                
                conflicts = sheets_manager.check_room_conflicts(
                    date=booking_data['date'],
                    start_time=booking_data['startTime'], 
                    end_time=booking_data['endTime'],
                    room=booking_data['room'],
                    exclude_row=booking_data.get('rowNumber')
                )
                
                # Tạo conflict message nếu có
                conflict_message = sheets_manager.generate_conflict_message(conflicts)
                booking_data['conflictMessage'] = conflict_message or ''
                
                logger.info(f"Conflict check completed. Found {len(conflicts)} conflicts.")
                
            except Exception as e:
                logger.warning(f"Could not check conflicts: {e}")
                booking_data['conflictMessage'] = ''

            # Xử lý booking với Discord bot
            if discord_bot:
                try:
                    # Bắn task async vào event loop bot (KHÔNG tạo loop mới!)
                    future = asyncio.run_coroutine_threadsafe(
                        discord_bot.process_new_booking(booking_data),
                        discord_bot.loop
                    )
                    # KHÔNG .result() nếu muốn trả về luôn cho Apps Script (không block)
                    logger.info(f"Booking for {email} scheduled to Discord bot event loop.")

                except Exception as e:
                    logger.error(f"Error scheduling Discord task: {e}")
                    # Vẫn trả 200 OK, để Apps Script không bị lỗi, nhưng báo chi tiết lỗi
                    return jsonify({
                        'status': 'received',
                        'message': 'Booking received but Discord processing failed',
                        'error': str(e)
                    }), 200
            else:
                logger.warning("Discord bot not available – booking not processed.")

            # Trả về thành công cho Apps Script
            return jsonify({
                'status': 'success',
                'message': 'Booking received and scheduled for processing',
                'rowNumber': booking_data.get('rowNumber'),
                'timestamp': datetime.now().isoformat()
            }), 200

        except Exception as e:
            logger.error(f"Webhook Error: {e}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500

    @app.route('/webhook/test', methods=['GET', 'POST'])
    def webhook_test():
        if request.method == 'GET':
            return jsonify({
                'message': 'Webhook test endpoint is working',
                'timestamp': datetime.now().isoformat(),
                'methods': ['GET', 'POST']
            })
        else:
            data = request.get_json() if request.is_json else {}
            logger.info(f"Test webhook received: {data}")
            return jsonify({
                'message': 'Test webhook received successfully',
                'received_data': data,
                'timestamp': datetime.now().isoformat()
            })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found', 'message': 'The requested endpoint does not exist'}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Method not allowed', 'message': 'This method is not allowed for this endpoint'}), 405

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

    return app

# Ví dụ khởi tạo app + bot
if __name__ == '__main__':
    # Giả sử đã có biến discord_bot (instance bot), hoặc để None nếu muốn test webhook độc lập
    app = create_app(discord_bot=None)
    app.run(host='0.0.0.0', port=5001, debug=True)
