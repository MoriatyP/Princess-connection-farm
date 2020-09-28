import gc
import os
import random
import time

from core.constant import MAIN_BTN, ZHUCAIDAN_BTN
# from core.log_handler import pcr_log
from core.pcr_config import debug
from core.safe_u2 import timeout
from core.utils import random_name, CreatIDnum
from ._base import BaseMixin


class LoginMixin(BaseMixin):
    """
    登录插片
    包含登录相关操作的脚本
    """

    @timeout(180, "start执行超时：超过3分钟")
    def start(self):
        """
        项目地址:https://github.com/bbpp222006/Princess-connection
        作者：bbpp222006
        协议：MIT License
        启动脚本，请确保已进入游戏页面。
        """
        while True:
            # 判断jgm进程是否在前台, 最多等待20秒，否则唤醒到前台
            if self.d.app_wait("com.bilibili.priconne", front=True, timeout=1):
                if not self.appRunning:
                    # 从后台换到前台，留一点反应时间
                    time.sleep(1)
                self.appRunning = True
                break
            else:
                self.app = self.d.session("com.bilibili.priconne")
                self.appRunning = False
                continue

    def do_login(self, ac, pwd):  # 执行登陆逻辑
        """
        :param ac:
        :param pwd:
        :return:
        """
        for retry in range(30):
            if not self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_edit_username_login").exists():
                time.sleep(2)
            else:
                break
        else:
            raise Exception("进入登陆页面失败！")
        self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_edit_username_login").click()
        self.d.clear_text()
        self.d.send_keys(str(ac))
        self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_edit_password_login").click()
        self.d.clear_text()
        self.d.send_keys(str(pwd))
        self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_buttonLogin").click()
        time.sleep(20)
        if debug:
            print("等待认证")
        while self.d(text="请滑动阅读协议内容").exists():
            if debug:
                print("发现协议")
            self.d.touch.down(814, 367).sleep(1).up(814, 367)
            self.d(text="同意").click()
            time.sleep(10)
        if debug:
            print("认证结束")
        if self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_edit_authentication_name").exists(timeout=0.1):
            return 1  # 说明要进行认证
        else:
            return 0  # 正常

    def login(self, ac, pwd):
        """
        项目地址:https://github.com/bbpp222006/Princess-connection
        作者：bbpp222006
        协议：MIT License
        :param ac:
        :param pwd:
        :return:
        """
        error_flag = 0
        try:
            # 看是否跳出主菜单
            self.lock_no_img(ZHUCAIDAN_BTN["bangzhu"], elseclick=[(871, 513), (165, 411), (591, 369)])
            self.lock_no_img('img/ok.bmp', elseclick=[(591, 369)], at=(495, 353, 687, 388))

            try_count = 0
            while True:
                try_count += 1
                if try_count % 10 == 0 and try_count > 500:
                    # 看一下会不会一直点右上角？
                    if self.last_screen is not None:
                        if self.is_exists(MAIN_BTN["liwu"], screen=self.last_screen):
                            # 已经登陆了老哥！
                            # 重 新 来 过
                            self.log.write_log("error", "可能出现了狂点右上角错误，换号")
                            self.lock_img(MAIN_BTN["liwu"], elseclick=MAIN_BTN["zhuye"], elsedelay=1)  # 回首页
                            self.change_acc()
                if try_count > 1000:
                    # 点了1000次了，重启吧
                    error_flag = 1
                    raise Exception("点了1000次右上角了，重启罢！")
                # todo 登陆失败报错：-32002 Client error: <> data: Selector [
                #  resourceId='com.bilibili.priconne:id/bsgamesdk_id_welcome_change'], method: None
                if self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_edit_authentication_name").exists(timeout=0.1):
                    return True
                if self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_id_welcome_change").exists():
                    self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_id_welcome_change").click()
                if self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_edit_username_login").exists():
                    self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_edit_username_login").click()
                    break
                else:
                    self.click(945, 13)
            return self.do_login(ac, pwd)
        except Exception as e:
            if error_flag:
                raise e
            # 异常重试登陆逻辑
            return self.do_login(ac, pwd)

    def auth(self, auth_name, auth_id):
        """
        项目地址:https://github.com/bbpp222006/Princess-connection
        作者：bbpp222006
        协议：MIT License
        :param auth_name:
        :param auth_id:
        :return:
        """
        self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_edit_authentication_name").click()
        self.d.clear_text()
        self.d.send_keys(str(auth_name))
        self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_edit_authentication_id_number").click()
        self.d.clear_text()
        self.d.send_keys(str(auth_id))
        self.d(resourceId="com.bilibili.priconne:id/bsgamesdk_authentication_submit").click()
        self.d(resourceId="com.bilibili.priconne:id/bagamesdk_auth_success_comfirm").click()

    @timeout(180, "login_auth登录超时，超过3分钟")
    def login_auth(self, ac, pwd):
        need_auth = self.login(ac=ac, pwd=pwd)
        if need_auth:
            auth_name, auth_id = random_name(), CreatIDnum()
            self.auth(auth_name=auth_name, auth_id=auth_id)

    def phone_privacy(self):
        """
        2020/7/10
        模拟器隐私函数
        '高'匿名 防记录(
        By：CyiceK
        :return:
        """

        def luhn_residue(digits):
            return sum(sum(divmod(int(d) * (1 + i % 2), 10))
                       for i, d in enumerate(digits[::-1])) % 10

        def _get_imei(n):
            part = ''.join(str(random.randrange(0, 9)) for _ in range(n - 1))
            res = luhn_residue('{}{}'.format(part, 0))
            return '{}{}'.format(part, -res % 10)

        # print("》》》匿名开始《《《")
        tmp_rand = []
        tmp_rand = random.sample(range(1, 10), 3)
        phone_model = {
            1: 'LIO-AN00',
            2: 'TAS-AN00',
            3: 'TAS-AL00',
            4: 'AUSU-AT00',
            5: 'AAA-SN00',
            6: 'GMI1910',
            7: 'G-OXLPix',
            8: 'AM-1000',
            9: 'G7',
        }
        phone_manufacturer = {
            1: 'HUAWEI',
            2: 'MEIZU',
            3: 'XIAOMI',
            4: 'OPPO',
            5: 'VIVO',
            6: 'MOTO',
            7: 'GooglePix',
            8: 'Redmi',
            9: 'LG',
        }
        os.system('cd adb & adb -s %s shell setprop ro.product.model %s' % (self.address, phone_model[tmp_rand[0]]))
        os.system(
            'cd adb & adb -s %s shell setprop ro.product.manufacturer %s' % (self.address, phone_manufacturer[tmp_rand[1]]))
        os.system('cd adb & adb -s %s shell setprop phone.imei %s' % (self.address, _get_imei(15)))
        os.system('cd adb & adb -s %s shell setprop ro.product.name %s' % (self.address, phone_model[tmp_rand[2]]))
        os.system('cd adb & adb -s %s shell setprop phone.imsi %s' % (self.address, _get_imei(15)))
        os.system('cd adb & adb -s %s shell setprop phone.linenum %s' % (self.address, _get_imei(11)))
        os.system('cd adb & adb -s %s shell setprop phone.simserial %s' % (self.address, _get_imei(20)))
        # print("》》》匿名完毕《《《")

    def change_acc(self):  # 切换账号
        self.lock_img(ZHUCAIDAN_BTN["bangzhu"], elseclick=[(871, 513)])  # 锁定帮助
        self.lock_img('img/ok.bmp', ifclick=[(591, 369)], elseclick=[(165, 411)], at=(495, 353, 687, 388))
        self.lock_no_img(ZHUCAIDAN_BTN["bangzhu"], elseclick=[(871, 513), (165, 411), (591, 369)])
        self.phone_privacy()
        gc.collect()
        # pcr_log(self.account).write_log(level='info', message='%s账号完成任务' % self.account)
        # pcr_log(self.account).server_bot("warning", "%s账号完成任务" % self.account)
