"""QuecPython编程套件主窗口"""
from threading import Thread
from pathlib import Path
from logging import getLogger
from serial import Serial
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

        # >>> 固件下载
        fw_label_frame = tk.LabelFrame(master=self, text='固件下载')
        fw_label_frame.pack(anchor=tk.NW, expand=True)
        for index in range(14):
            fw_label_frame.columnconfigure(index, weight=1)

        serial_label = tk.Label(fw_label_frame, text='串口:')
        serial_label.grid(row=0, column=0, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.serial_combobox = ttk.Combobox(master=fw_label_frame, postcommand=self.list_valid_ports)
        self.serial_combobox.grid(row=0, column=1, ipadx=40, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.list_valid_ports()

        baudrate_label = tk.Label(fw_label_frame, text='波特率:')
        baudrate_label.grid(row=0, column=2, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.baudrate_combobox = ttk.Combobox(master=fw_label_frame, values=Serial.BAUDRATES, width=7)
        self.baudrate_combobox.set('115200')
        self.baudrate_combobox.grid(row=0, column=3, sticky=tk.W, padx=(5, 5), pady=(5, 5))

        stopbits_label = tk.Label(fw_label_frame, text='停止位:')
        stopbits_label.grid(row=0, column=4, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.stopbits_combobox = ttk.Combobox(master=fw_label_frame, values=Serial.STOPBITS, width=5)
        self.stopbits_combobox.set('1')
        self.stopbits_combobox.grid(row=0, column=5, sticky=tk.W, padx=(5, 5), pady=(5, 5))

        parity_label = tk.Label(fw_label_frame, text='校验:')
        parity_label.grid(row=0, column=6, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.parity_combobox = ttk.Combobox(master=fw_label_frame, values=Serial.PARITIES, width=5)
        self.parity_combobox.set('N')
        self.parity_combobox.grid(row=0, column=7, sticky=tk.W, padx=(5, 5), pady=(5, 5))

        bytesize_label = tk.Label(fw_label_frame, text='数据位:')
        bytesize_label.grid(row=0, column=8, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.bytesize_combobox = ttk.Combobox(master=fw_label_frame, values=Serial.BYTESIZES, width=5)
        self.bytesize_combobox.set('8')
        self.bytesize_combobox.grid(row=0, column=9, sticky=tk.W, padx=(5, 5), pady=(5, 5))

        flow_control_label = tk.Label(fw_label_frame, text='流控:')
        flow_control_label.grid(row=0, column=10, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.flow_control_combobox = ttk.Combobox(master=fw_label_frame, values=['No', 'HW', 'SW'], width=5)
        self.flow_control_combobox.set('No')
        self.flow_control_combobox.grid(row=0, column=11, sticky=tk.W, padx=(5, 5), pady=(5, 5))

        fw_file_path_label = tk.Label(fw_label_frame, text='固件文件:')
        fw_file_path_label.grid(row=1, column=0, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.firmware_file_path_stringvar = tk.StringVar()
        fw_file_path_entry = tk.Entry(fw_label_frame, textvariable=self.firmware_file_path_stringvar, state='readonly')
        fw_file_path_entry.grid(row=1, column=1, columnspan=11, sticky=tk.EW, padx=(5, 5), pady=(5, 5))
        self.fw_file_choose_button = tk.Button(fw_label_frame, text='选择路径',
                                               command=self.get_firmware_file_path_handler)
        self.fw_file_choose_button.grid(row=1, column=12, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.fw_download_button = tk.Button(fw_label_frame, text='下载固件',
                                            command=self.download_firmware_thread_worker)
        self.fw_download_button.grid(row=1, column=13, sticky=tk.W, padx=(5, 5), pady=(5, 5))

        progress_label = tk.Label(fw_label_frame, text='下载进度:')
        progress_label.grid(row=2, column=0, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.bar = ttk.Progressbar(master=fw_label_frame, maximum=100)
        self.bar.grid(row=2, column=1, columnspan=11, sticky=tk.EW, padx=(5, 5), pady=(5, 5))
        self.progress_stringvar = tk.StringVar()
        self.progress_stringvar.set('0%')
        progress_entry = tk.Label(fw_label_frame, textvariable=self.progress_stringvar)
        progress_entry.grid(row=2, column=12, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        self.log_stringvar = tk.StringVar()
        self.log_stringvar.set('就绪')
        log_entry = tk.Label(fw_label_frame, textvariable=self.log_stringvar)
        log_entry.grid(row=2, column=13, sticky=tk.W, padx=(5, 5), pady=(5, 5))
        # <<<

    def list_valid_ports(self):
        rv = []
        for p in list_ports.comports():
            rv.append("{}-{}".format(p.device, p.description))

        self.serial_combobox['value'] = rv
        current_port_str = self.serial_combobox.get()
        if current_port_str in rv:
            self.serial_combobox.set(current_port_str)
        else:
            self.serial_combobox.current(0)

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
        return self.serial_combobox.get().split('-')[0]

    def download_firmware_handler(self):
        logger.info('enter download_firmware_handler method.')

        self.fw_file_choose_button.config(state=tk.DISABLED)
        self.fw_download_button.config(state=tk.DISABLED)
        self.bar["value"] = 0
        self.progress_stringvar.set("{}%".format(0))
        self.log_stringvar.set("就绪")
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
                    self.log_stringvar.set('请重启板子，按RESET')
                    self.update()
                    continue
                self.progress_stringvar.set("{}%".format(data))
                self.bar["value"] = data
                self.log_stringvar.set('正在下载中')
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
            self.log_stringvar.set('已完成')
            self.fw_file_choose_button.config(state=tk.ACTIVE)
            self.fw_download_button.config(state=tk.ACTIVE)

    def download_firmware_thread_worker(self):
        worker = Thread(target=self.download_firmware_handler)
        worker.start()


def open_quecview():
    get_workbench().show_view('QuecView')

