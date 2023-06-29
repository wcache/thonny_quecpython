"""QuecPython编程套件主窗口"""
import time
from threading import Thread
from pathlib import Path
from logging import getLogger
from serial.tools import list_ports
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from thonny import get_workbench
from .api import download_firmware_api
from .fw import DownloadLogFile
from .fw.utils import get_com_port


logger = getLogger(__name__)


class QuecView(tk.Frame):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('borderwidth', 10)
        super().__init__(*args, **kwargs)

        # >>> 串口
        label_frame1 = tk.LabelFrame(master=self, text='串口参数设置')
        label_frame1.grid(row=0, column=0, columnspan=13, sticky=tk.NSEW, pady=(0, 10))

        label1 = tk.Label(label_frame1, text='串口:')
        label1.grid(row=0, column=0, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))
        self.serial_list = ttk.Combobox(master=label_frame1, postcommand=self.list_valid_ports)
        self.serial_list.grid(row=0, column=1, ipadx=40, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))
        self.list_valid_ports()
        # <<<

        # >>> 固件下载
        label_frame2 = tk.LabelFrame(master=self, text='固件下载')
        label_frame2.grid(row=1, column=0, columnspan=13, sticky=tk.NSEW, pady=(0, 10))

        label2 = tk.Label(label_frame2, text='固件文件:')
        label2.grid(row=0, column=0, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))
        self.firmware_file_path_stringvar = tk.StringVar()
        entry1 = tk.Entry(label_frame2, textvariable=self.firmware_file_path_stringvar, width=100, state='readonly')
        entry1.grid(row=0, column=1, columnspan=10, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))
        self.button1 = tk.Button(label_frame2, text='选择路径', command=self.get_firmware_file_path_handler)
        self.button1.grid(row=0, column=11, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))
        self.button2 = tk.Button(label_frame2, text='下载固件', command=self.download_firmware_thread_worker)
        self.button2.grid(row=0, column=12, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))

        label3 = tk.Label(label_frame2, text='下载进度:')
        label3.grid(row=1, column=0, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))
        self.bar = ttk.Progressbar(master=label_frame2, maximum=100)
        self.bar.grid(row=1, column=1, columnspan=10, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))
        self.progress_text_var = tk.StringVar()
        self.progress_text_var.set('0%')
        progress_entry = tk.Label(label_frame2, textvariable=self.progress_text_var)
        progress_entry.grid(row=1, column=11, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))
        self.log_text_var = tk.StringVar()
        self.log_text_var.set('就绪')
        log_entry = tk.Label(label_frame2, textvariable=self.log_text_var)
        log_entry.grid(row=1, column=12, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5))
        # <<<

    def list_valid_ports(self):
        rv = []
        for p in list_ports.comports():
            rv.append("{}-{}".format(p.device, p.description))

        self.serial_list['value'] = rv
        current_port_str = self.serial_list.get()
        if current_port_str in rv:
            self.serial_list.set(current_port_str)
        else:
            self.serial_list.current(0)

    def get_firmware_file_path_handler(self):
        firmware_file_path = filedialog.askopenfilename(title='请选择文件')
        self.firmware_file_path_stringvar.set(firmware_file_path)

    def get_validated_com_port(self, firmware_file_path):
        comport = get_com_port(Path(firmware_file_path))
        if comport is None:
            raise Exception('未检测到与该固件匹配的设备（模块），请连接对应的设备再重试。')

        if comport in ("NB_DOWNLOAD", "mbn_DOWNLOAD"):
            comport = self.get_port_from_user_choose()

        return comport

    def get_port_from_user_choose(self):
        # TODO: 用户指定烧录串口
        return self.serial_list.get().split('-')[0]

    def download_firmware_handler(self):
        logger.info('enter download_firmware_handler method.')

        self.button1.config(state=tk.DISABLED)
        self.button2.config(state=tk.DISABLED)
        self.bar["value"] = 0
        self.progress_text_var.set("{}%".format(0))
        self.log_text_var.set("就绪")
        self.update()

        try:
            firmware_file_path = self.firmware_file_path_stringvar.get()
            logger.info('firmware_file_path: {}'.format(firmware_file_path))
            if not firmware_file_path:
                raise Exception('not firmware file path selected!')
            comport = self.get_validated_com_port(firmware_file_path)
            logger.info('comport: {}'.format(comport))
            for data in download_firmware_api(firmware_file_path, comport):
                if data == "RESET":
                    self.log_text_var.set('请重启板子，按RESET')
                    self.update()
                    continue
                self.progress_text_var.set("{}%".format(data))
                self.bar["value"] = data
                self.log_text_var.set('正在下载中')
                self.update()
        except Exception as e:
            messagebox.showerror(
                title='Error',
                message='Download Firmware Error!\n{}\nsee log: {}'.format(str(e), DownloadLogFile.log_file_path),
                master=self
            )
        else:
            messagebox.showinfo(
                title='Information',
                message='Download Firmware Successfully!',
                master=self
            )
        finally:
            self.log_text_var.set('已完成')
            self.button1.config(state=tk.ACTIVE)
            self.button2.config(state=tk.ACTIVE)

    def download_firmware_thread_worker(self):
        worker = Thread(target=self.download_firmware_handler)
        worker.start()


def open_quecview():
    get_workbench().show_view('QuecView')

