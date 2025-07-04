"""
Discord Commands cho Quản lý Kho
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
from .kho_manager import KhoManager
from config import Config

logger = logging.getLogger(__name__)

class KhoCommands(commands.Cog):
    """
    Discord Commands cho quản lý kho vật tư/nguyên liệu
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.kho_manager = KhoManager()
        self.allowed_channel = Config.KHO_CHANNEL_NAME
        logger.info(f"KhoCommands cog initialized - allowed channel: #{self.allowed_channel}")
    
    def _is_allowed_channel(self, ctx: commands.Context) -> bool:
        """
        Kiểm tra xem lệnh có được thực hiện trong kênh được phép không
        
        Args:
            ctx: Discord command context
            
        Returns:
            bool: True nếu được phép, False nếu không
        """
        if not hasattr(ctx.channel, 'name'):
            return False
        return ctx.channel.name == self.allowed_channel
    
    async def _send_channel_error(self, ctx: commands.Context):
        """
        Gửi thông báo lỗi khi lệnh được sử dụng sai kênh
        """
        embed = discord.Embed(
            title="❌ Kênh Không Hợp Lệ",
            color=discord.Color.red(),
            description=f"🚫 Lệnh quản lý kho chỉ có thể sử dụng trong kênh **#{self.allowed_channel}**\n"
                       f"📍 Vui lòng chuyển sang kênh **#{self.allowed_channel}** để sử dụng các lệnh kho."
        )
        await ctx.send(embed=embed, delete_after=10)
    
    def _parse_command_args(self, args: str, expected_parts: int) -> Optional[list]:
        """
        Parse command arguments với format: part1 - part2 - part3
        
        Args:
            args (str): Chuỗi arguments
            expected_parts (int): Số phần mong đợi
            
        Returns:
            list: Danh sách các phần đã parse, hoặc None nếu lỗi
        """
        if not args:
            return None
            
        parts = [p.strip() for p in args.split("-")]
        if len(parts) != expected_parts:
            return None
            
        return parts
    
    @commands.command(name="nhapkho")
    async def nhap_kho(self, ctx: commands.Context, *, args: str = None):
        """
        Nhập kho nguyên liệu
        
        Cú pháp: /nhapkho Tên nguyên liệu - SL nhập - Tổng SL
        Ví dụ: /nhapkho Cà phê - 10 - 50
        """
        # Kiểm tra kênh trước tiên
        if not self._is_allowed_channel(ctx):
            await self._send_channel_error(ctx)
            return
            
        if not args:
            embed = discord.Embed(
                title="⚠️ Sai định dạng!",
                color=discord.Color.orange(),
                description="📝 **Cú pháp:** `/nhapkho Tên nguyên liệu - SL nhập - Tổng SL`"
                            "\n"
                           "📋 **Ví dụ:** `/nhapkho Cà phê - 10 - 50`"
            )
            await ctx.send(embed=embed)
            return
        
        # Parse arguments
        parts = self._parse_command_args(args, 3)
        if not parts:
            embed = discord.Embed(
                title="⚠️ Sai định dạng!",
                color=discord.Color.orange(),
                description="📝 **Cú pháp:** `/nhapkho Tên nguyên liệu - SL nhập - Tổng SL`\n"
                           "📋 **Ví dụ:** `/nhapkho Cà phê - 10 - 50`"
            )
            await ctx.send(embed=embed)
            return
        
        try:
            ten_nguyen_lieu, so_luong_nhap_str, tong_so_luong = parts
            so_luong_nhap = int(so_luong_nhap_str)  # Validate số nguyên
            
            # Lấy username
            username = ctx.author.display_name or ctx.author.name
            
            # Gửi request đến backend
            result = self.kho_manager.nhap_kho(
                ten_nguyen_lieu=ten_nguyen_lieu,
                so_luong_nhap=so_luong_nhap,
                tong_so_luong=tong_so_luong,
                nguoi_nhap=username
            )
            
            # Xử lý response
            if result.get("status") == "success":
                embed = discord.Embed(
                    title="✅ Nhập Kho Thành Công",
                    color=discord.Color.green(),
                    description=f"**Nguyên liệu:** {ten_nguyen_lieu}\n"
                               f"**Số lượng nhập:** {so_luong_nhap}\n"
                               f"**Tổng số lượng:** {tong_so_luong}\n"
                               f"**Người nhập:** {username}"
                )
                await ctx.send(embed=embed)
            else:
                error_msg = result.get('message', 'Không rõ nguyên nhân')
                await ctx.send(f"⚠️ **Lỗi từ server:** {error_msg}")
                
        except ValueError:
            await ctx.send("⚠️ **Lỗi:** Số lượng nhập phải là số nguyên!")
        except Exception as e:
            logger.error(f"Error in nhap_kho command: {e}")
            await ctx.send(f"❌ **Lỗi xử lý nhập kho:** {str(e)}")
    
    @commands.command(name="xuatkho")
    async def xuat_kho(self, ctx: commands.Context, *, args: str = None):
        """
        Xuất kho nguyên liệu
        
        Cú pháp: /xuatkho Tên nguyên liệu - SL xuất - SL còn lại
        Ví dụ: /xuatkho Cà phê - 5 - 45
        """
        # Kiểm tra kênh trước tiên
        if not self._is_allowed_channel(ctx):
            await self._send_channel_error(ctx)
            return
            
        if not args:
            embed = discord.Embed(
                title="⚠️ Sai định dạng!",
                color=discord.Color.orange(),
                description="📝 **Cú pháp:** `/xuatkho Tên nguyên liệu - SL xuất - SL còn lại`\n"
                           "📋 **Ví dụ:** `/xuatkho Cà phê - 5 - 45`"
            )
            await ctx.send(embed=embed)
            return
        
        # Parse arguments
        parts = self._parse_command_args(args, 3)
        if not parts:
            embed = discord.Embed(
                title="⚠️ Sai định dạng!",
                color=discord.Color.orange(),
                description="📝 **Cú pháp:** `/xuatkho Tên nguyên liệu - SL xuất - SL còn lại`\n"
                           "📋 **Ví dụ:** `/xuatkho Cà phê - 5 - 45`"
            )
            await ctx.send(embed=embed)
            return
        
        try:
            ten_nguyen_lieu, so_luong_xuat_str, so_luong_con_lai_str = parts
            so_luong_xuat = int(so_luong_xuat_str)
            so_luong_con_lai = int(so_luong_con_lai_str)
            
            # Lấy username
            username = ctx.author.display_name or ctx.author.name
            
            # Gửi request đến backend
            result = self.kho_manager.xuat_kho(
                ten_nguyen_lieu=ten_nguyen_lieu,
                so_luong_xuat=so_luong_xuat,
                so_luong_con_lai=so_luong_con_lai,
                nguoi_xuat=username
            )
            
            # Xử lý response
            if result.get("status") == "success":
                embed = discord.Embed(
                    title="✅ Xuất Kho Thành Công",
                    color=discord.Color.blue(),
                    description=f"**Nguyên liệu:** {ten_nguyen_lieu}\n"
                               f"**Số lượng xuất:** {so_luong_xuat}\n"
                               f"**Số lượng còn lại:** {so_luong_con_lai}\n"
                               f"**Người xuất:** {username}"
                )
                await ctx.send(embed=embed)
            else:
                error_msg = result.get('message', 'Không rõ nguyên nhân')
                await ctx.send(f"⚠️ **Lỗi từ server:** {error_msg}")
                
        except ValueError:
            await ctx.send("⚠️ **Lỗi:** Số lượng xuất và còn lại phải là số nguyên!")
        except Exception as e:
            logger.error(f"Error in xuat_kho command: {e}")
            await ctx.send(f"❌ **Lỗi xử lý xuất kho:** {str(e)}")
    
    @commands.command(name="chebien")
    async def che_bien(self, ctx: commands.Context, *, args: str = None):
        """
        Chế biến nguyên liệu
        
        Cú pháp: /chebien Tên nguyên liệu - Dung tích có được
        Ví dụ: /chebien Cà phê rang - 2 lít
        """
        # Kiểm tra kênh trước tiên
        if not self._is_allowed_channel(ctx):
            await self._send_channel_error(ctx)
            return
            
        if not args:
            embed = discord.Embed(
                title="⚠️ Sai định dạng!",
                color=discord.Color.orange(),
                description="📝 **Cú pháp:** `/chebien Tên nguyên liệu - Dung tích có được`\n"
                           "📋 **Ví dụ:** `/chebien Cà phê rang - 2 lít`"
            )
            await ctx.send(embed=embed)
            return
        
        # Parse arguments
        parts = self._parse_command_args(args, 2)
        if not parts:
            embed = discord.Embed(
                title="⚠️ Sai định dạng!",
                color=discord.Color.orange(),
                description="📝 **Cú pháp:** `/chebien Tên nguyên liệu - Dung tích có được`\n"
                           "📋 **Ví dụ:** `/chebien Cà phê rang - 2 lít`"
            )
            await ctx.send(embed=embed)
            return
        
        try:
            ten_nguyen_lieu, dung_tich = parts
            
            # Lấy username
            username = ctx.author.display_name or ctx.author.name
            
            # Gửi request đến backend
            result = self.kho_manager.che_bien(
                ten_nguyen_lieu=ten_nguyen_lieu,
                dung_tich=dung_tich,
                nguoi_che_bien=username
            )
            
            # Xử lý response
            if result.get("status") == "success":
                embed = discord.Embed(
                    title="✅ Chế Biến Thành Công",
                    color=discord.Color.orange(),
                    description=f"**Nguyên liệu:** {ten_nguyen_lieu}\n"
                               f"**Dung tích có được:** {dung_tich}\n"
                               f"**Người chế biến:** {username}"
                )
                await ctx.send(embed=embed)
            else:
                error_msg = result.get('message', 'Không rõ nguyên nhân')
                await ctx.send(f"⚠️ **Lỗi từ server:** {error_msg}")
                
        except Exception as e:
            logger.error(f"Error in che_bien command: {e}")
            await ctx.send(f"❌ **Lỗi xử lý chế biến:** {str(e)}")
    
    @commands.command(name="huynguyenlieu")
    async def huy_nguyen_lieu(self, ctx: commands.Context, *, args: str = None):
        """
        Hủy nguyên liệu
        
        Cú pháp: /huynguyenlieu Tên nguyên liệu - Số lượng/trọng lượng - lý do huỷ
        Ví dụ: /huynguyenlieu Cà phê - 1kg - hết hạn
        """
        # Kiểm tra kênh trước tiên
        if not self._is_allowed_channel(ctx):
            await self._send_channel_error(ctx)
            return
            
        if not args:
            embed = discord.Embed(
                title="⚠️ Sai định dạng!",
                color=discord.Color.orange(),
                description="📝 **Cú pháp:** `/huynguyenlieu Tên nguyên liệu - Số lượng/trọng lượng - lý do huỷ`\n"
                           "📋 **Ví dụ:** `/huynguyenlieu Cà phê - 1kg - hết hạn`"
            )
            await ctx.send(embed=embed)
            return
        
        # Parse arguments
        parts = self._parse_command_args(args, 3)
        if not parts:
            embed = discord.Embed(
                title="⚠️ Sai định dạng!",
                color=discord.Color.orange(),
                description="📝 **Cú pháp:** `/huynguyenlieu Tên nguyên liệu - Số lượng/trọng lượng - lý do huỷ`\n"
                           "📋 **Ví dụ:** `/huynguyenlieu Cà phê - 1kg - hết hạn`"
            )
            await ctx.send(embed=embed)
            return
        
        try:
            ten_nguyen_lieu, so_luong_huy, ly_do = parts
            
            # Lấy username
            username = ctx.author.display_name or ctx.author.name
            
            # Gửi request đến backend
            result = self.kho_manager.huy_nguyen_lieu(
                ten_nguyen_lieu=ten_nguyen_lieu,
                so_luong_huy=so_luong_huy,
                ly_do=ly_do,
                nguoi_huy=username
            )
            
            # Xử lý response
            if result.get("status") == "success":
                embed = discord.Embed(
                    title="✅ Hủy Nguyên Liệu Thành Công",
                    color=discord.Color.red(),
                    description=f"**Nguyên liệu:** {ten_nguyen_lieu}\n"
                               f"**Số lượng hủy:** {so_luong_huy}\n"
                               f"**Lý do:** {ly_do}\n"
                               f"**Người hủy:** {username}"
                )
                await ctx.send(embed=embed)
            else:
                error_msg = result.get('message', 'Không rõ nguyên nhân')
                await ctx.send(f"⚠️ **Lỗi từ server:** {error_msg}")
                
        except Exception as e:
            logger.error(f"Error in huy_nguyen_lieu command: {e}")
            await ctx.send(f"❌ **Lỗi xử lý hủy nguyên liệu:** {str(e)}")
    
    @commands.command(name="khostatus")
    async def kho_status(self, ctx: commands.Context):
        """
        Kiểm tra trạng thái cấu hình kho
        """
        # Kiểm tra kênh trước tiên
        if not self._is_allowed_channel(ctx):
            await self._send_channel_error(ctx)
            return
            
        status = self.kho_manager.get_status()
        
        embed = discord.Embed(
            title="📊 Trạng Thái Hệ Thống Kho",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🔗 Cấu hình Apps Script",
            value="✅ Đã cấu hình" if status['kho_configured'] else "❌ Chưa cấu hình",
            inline=True
        )
        
        if status['kho_configured']:
            embed.add_field(
                name="🌐 URL",
                value=f"`{status['kho_url'][:50]}...`" if len(status['kho_url']) > 50 else f"`{status['kho_url']}`",
                inline=False
            )
        
        embed.add_field(
            name="⏱️ Timeout",
            value=f"{status['timeout']}s",
            inline=True
        )
        
        embed.add_field(
            name="🔄 Max Retries",
            value=str(status['max_retries']),
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="khohelp")
    async def kho_help(self, ctx: commands.Context):
        """
        Hiển thị hướng dẫn sử dụng các lệnh kho
        """
        # Kiểm tra kênh trước tiên
        if not self._is_allowed_channel(ctx):
            await self._send_channel_error(ctx)
            return
            
        embed = discord.Embed(
            title="📦 Hướng Dẫn Lệnh Quản Lý Kho",
            color=discord.Color.gold(),
            description=f"Danh sách các lệnh quản lý kho vật tư/nguyên liệu\n"
                       f"🔒 **Chỉ hoạt động trong kênh #{self.allowed_channel}**\n"
        )
        
        embed.add_field(
            name="📥 `/nhapkho`",
            value="**Cú pháp:** `Tên nguyên liệu - SL nhập - Tổng SL`"
            "\n"
                  "**Ví dụ:** `/nhapkho Cà phê - 10 - 50`",
            inline=False
        )
        
        embed.add_field(
            name="📤 `/xuatkho`",
            value="**Cú pháp:** `Tên nguyên liệu - SL xuất - SL còn lại`"
            "\n"
                  "**Ví dụ:** `/xuatkho Cà phê - 5 - 45`",
            inline=False
        )
        
        embed.add_field(
            name="🔄 `/chebien`",
            value="**Cú pháp:** `Tên nguyên liệu - Dung tích có được`"
            "\n"
                  "**Ví dụ:** `/chebien Cà phê rang - 2 lít`",
            inline=False
        )
        
        embed.add_field(
            name="🗑️ `/huynguyenlieu`",
            value="**Cú pháp:** `Tên nguyên liệu - Số lượng/trọng lượng - lý do huỷ`"
            "\n"
                  "**Ví dụ:** `/huynguyenlieu Cà phê - 1kg - hết hạn`",
            inline=False
        )
        
        embed.add_field(
            name="📊 `/khostatus`",
            value="Kiểm tra trạng thái cấu hình hệ thống kho",
            inline=False
        )
        
        embed.add_field(
            name="❓ `/khohelp`",
            value="Hiển thị hướng dẫn này",
            inline=False
        )
        
        embed.set_footer(text="💡 Lưu ý: Sử dụng dấu '-' để phân tách các phần trong lệnh")
        
        await ctx.send(embed=embed)

# Setup function để load cog
async def setup(bot):
    await bot.add_cog(KhoCommands(bot))
