"""
Kho Manager - Quản lý giao tiếp với Google Apps Script backend cho chức năng kho
"""

import requests
import logging
from typing import Dict, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class KhoManager:
    """
    Quản lý giao tiếp với Google Apps Script backend cho chức năng quản lý kho
    """
    
    def __init__(self, kho_url: Optional[str] = None):
        """
        Khởi tạo Kho Manager
        
        Args:
            kho_url (str, optional): URL của Apps Script Web App cho kho
        """
        self.kho_url = kho_url or getattr(Config, 'KHO_WEB_APP_URL', None)
        
        if not self.kho_url:
            logger.warning("KHO_WEB_APP_URL not configured. Kho functions will be disabled.")
        
        # Timeout settings
        self.timeout = getattr(Config, 'KHO_TIMEOUT', 30)
        self.max_retries = getattr(Config, 'KHO_MAX_RETRIES', 3)
    
    def send_kho_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gửi request đến Google Apps Script backend cho kho
        
        Args:
            data (dict): Dữ liệu cần gửi
            
        Returns:
            dict: Response từ backend
        """
        if not self.kho_url:
            return {
                "status": "error",
                "message": "KHO_WEB_APP_URL not configured"
            }
        
        try:
            logger.info(f"Sending kho request: {data}")
            
            response = requests.post(
                self.kho_url,
                json=data,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Kho response: {result}")
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout when sending kho request: {data}")
            return {
                "status": "error",
                "message": "Request timeout - Apps Script không phản hồi"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error when sending kho request: {e}")
            return {
                "status": "error",
                "message": f"Lỗi kết nối: {str(e)}"
            }
            
        except ValueError as e:
            logger.error(f"JSON parse error from kho response: {e}")
            return {
                "status": "error",
                "message": "Response không đúng định dạng JSON"
            }
            
        except Exception as e:
            logger.error(f"Unexpected error when sending kho request: {e}")
            return {
                "status": "error",
                "message": f"Lỗi không xác định: {str(e)}"
            }
    
    def nhap_kho(self, ten_nguyen_lieu: str, so_luong_nhap: int, 
                 tong_so_luong: str, nguoi_nhap: str) -> Dict[str, Any]:
        """
        Nhập kho nguyên liệu
        
        Args:
            ten_nguyen_lieu (str): Tên nguyên liệu
            so_luong_nhap (int): Số lượng nhập
            tong_so_luong (str): Tổng số lượng sau khi nhập
            nguoi_nhap (str): Người thực hiện nhập kho
            
        Returns:
            dict: Kết quả từ backend
        """
        data = {
            "action": "nhapkho",
            "ten_nguyen_lieu": ten_nguyen_lieu,
            "so_luong_nhap": so_luong_nhap,
            "tong_so_luong": tong_so_luong,
            "nguoi_nhap": nguoi_nhap
        }
        
        return self.send_kho_request(data)
    
    def xuat_kho(self, ten_nguyen_lieu: str, so_luong_xuat: int,
                 so_luong_con_lai: int, nguoi_xuat: str) -> Dict[str, Any]:
        """
        Xuất kho nguyên liệu
        
        Args:
            ten_nguyen_lieu (str): Tên nguyên liệu
            so_luong_xuat (int): Số lượng xuất
            so_luong_con_lai (int): Số lượng còn lại
            nguoi_xuat (str): Người thực hiện xuất kho
            
        Returns:
            dict: Kết quả từ backend
        """
        data = {
            "action": "xuatkho",
            "ten_nguyen_lieu": ten_nguyen_lieu,
            "so_luong_xuat": so_luong_xuat,
            "so_luong_con_lai": so_luong_con_lai,
            "nguoi_xuat": nguoi_xuat
        }
        
        return self.send_kho_request(data)
    
    def che_bien(self, ten_nguyen_lieu: str, dung_tich: str, 
                 nguoi_che_bien: str) -> Dict[str, Any]:
        """
        Chế biến nguyên liệu
        
        Args:
            ten_nguyen_lieu (str): Tên nguyên liệu
            dung_tich (str): Dung tích có được
            nguoi_che_bien (str): Người thực hiện chế biến
            
        Returns:
            dict: Kết quả từ backend
        """
        data = {
            "action": "chebien",
            "ten_nguyen_lieu": ten_nguyen_lieu,
            "dung_tich": dung_tich,
            "nguoi_che_bien": nguoi_che_bien
        }
        
        return self.send_kho_request(data)
    
    def huy_nguyen_lieu(self, ten_nguyen_lieu: str, so_luong_huy: str,
                        ly_do: str, nguoi_huy: str) -> Dict[str, Any]:
        """
        Hủy nguyên liệu
        
        Args:
            ten_nguyen_lieu (str): Tên nguyên liệu
            so_luong_huy (str): Số lượng/trọng lượng hủy
            ly_do (str): Lý do hủy
            nguoi_huy (str): Người thực hiện hủy
            
        Returns:
            dict: Kết quả từ backend
        """
        data = {
            "action": "huynguyenlieu",
            "ten_nguyen_lieu": ten_nguyen_lieu,
            "so_luong_huy": so_luong_huy,
            "ly_do": ly_do,
            "nguoi_huy": nguoi_huy
        }
        
        return self.send_kho_request(data)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Lấy trạng thái cấu hình kho
        
        Returns:
            dict: Thông tin trạng thái
        """
        return {
            "kho_url": self.kho_url,
            "kho_configured": bool(self.kho_url),
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
