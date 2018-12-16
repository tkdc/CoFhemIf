#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

FHEM server http interface

Copyright (C) 2018 Thomas Katemann

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import datetime
import threading
import requests

__title__ = 'FhemIf'
__version__ = '1.1.0'
__author__ = 'Thomas Katemann'
__copyright__ = 'Copyright 2018 Thomas Katemann'
__license__ = 'GPLv3'


class CoFhemIf(object):
    def __init__(self):

        print('--- CoFhemIf Init ---')

        # network configuration
        self.b_print = True
        self.ip_address = '192.168.178.31'
        self.ip_port = '8082'

        # device configuration
        self.a_swt_dev = ['05_LamBed', '08_LamCen', '01_MpBase', '04_MedTow', '06_MedKit']  # switches
        self.a_temp_dev = ['01_LivRoom', '02_Bath', '03_Kitchen', '02_OutdoorTH']  # temp control and sensors
        self.a_temp_dev_name = ['LivRoom', 'Bath', 'Kitchen', 'Outdoor']  # temp control and sensors

        # http request templates
        self.str_http_resp = ''
        self.csrf_token = ''
        self.str_csrf_req_tmpl = 'http://%s:%s/fhem?XHR=1'
        self.str_swt_cmd_tmpl = 'http://%s:%s/fhem?cmd.%s=set%s20%s20%s&XHR=1&fwcsrf=%s&fw_id=157'
        self.str_temp_dev_req_tmpl = 'http://%s:%s/fhem?detail=%s'
        self.str_temp_set_tmpl = 'http://%s:%s/fhem?cmd=set%s20%s20%s20%s&XHR=1&fwcsrf=%s&fw_id=2247'

        self.str_des_temp1 = 'informId="%s-desired-temp">'
        self.str_des_temp2 = '</div>'
        self.str_meas_temp1 = 'informId="%s-measured-temp">'
        self.str_meas_temp2 = '</div>'
        self.str_actor1 = 'informId="%s-actuator">'
        self.str_actor2 = '</div>'

        self.str_od_temp1 = 'informId="%s-temperature">'
        self.str_od_temp2 = '</div>'
        self.str_od_hum1 = 'informId="%s-humidity">'
        self.str_od_hum2 = '</div>'

        # value response storage
        self.d_value_01 = [0.0, 0.0, 0.0, 0.0]
        self.d_value_02 = [0.0, 0.0, 0.0, 0.0]
        self.d_value_03 = [0.0, 0.0, 0.0, None]
        self.a_str_value_01 = ['', '', '', '']
        self.a_str_value_02 = ['', '', '', '']
        self.a_str_value_03 = ['', '', '', '']

        # init, cycle and event config
        self.idx_ct_cnt = 0
        self.b_init = True
        self.tm_ct_init = 3
        self.tm_ct_norm = 30

        self.ev_send_info = EventCall()
        self.cyclic_thread_0()

        print('--- CoFhemIf Init Finished ---')

    def get_cmd_info(self, str_print):
        """

        :param str_print:
        """
        if self.b_print:
            str_cur_time = str(datetime.datetime.time(datetime.datetime.now()))
            print(str_cur_time + ' ' + str_print)

    def cyclic_thread_0(self):
        """
        cyclic thread 2: (ts = 1 sec)
        """
        if self.b_init:
            tm_ct_cur = self.tm_ct_init

            if self.idx_ct_cnt >= 1:
                self.idx_ct_cnt = 0

                self.get_fhem_csrf()
                for idx_dev in range(4):
                    self.get_fhem_dev_prop(idx_dev, True)
                self.b_init = False

            else:
                self.idx_ct_cnt = self.idx_ct_cnt + 1

        else:
            tm_ct_cur = self.tm_ct_norm

            self.get_fhem_dev_prop(self.idx_ct_cnt)

            if self.idx_ct_cnt >= 3:
                self.idx_ct_cnt = 0
            else:
                self.idx_ct_cnt = self.idx_ct_cnt + 1

        threading.Timer(tm_ct_cur, self.cyclic_thread_0).start()

    def get_fhem_csrf(self):
        """

        """
        str_url = self.str_csrf_req_tmpl % (self.ip_address, self.ip_port)
        str_headers = self.send_http_req(str_url, 'headers')
        self.csrf_token = str_headers.get('X-FHEM-csrfToken')
        self.get_cmd_info('FHEM: csrf_token: ' + str(self.csrf_token))

    def make_swt_cmd(self, idx_swt, str_action):
        """

        :param idx_swt:
        :param str_action:
        :return:
        """
        return self.str_swt_cmd_tmpl % (self.ip_address, self.ip_port, self.a_swt_dev[idx_swt], '%',
                                        self.a_swt_dev[idx_swt] + '%', str_action, self.csrf_token)

    def make_temp_cmd(self, idx_dev, str_action, value):
        """

        :param idx_dev:
        :param str_action:
        :param value:
        :return:
        """
        return self.str_temp_set_tmpl % (self.ip_address, self.ip_port, '%', self.a_temp_dev[idx_dev]+'%',
                                         str_action+'%', str(value), self.csrf_token)

    def set_fhem_swt(self, idx_swt, str_action):
        """

        :param idx_swt:
        :param str_action:
        """
        self.send_http_req(self.make_swt_cmd(idx_swt, str_action))
        self.get_cmd_info('FHEM: set switch: ' + str(self.a_swt_dev[idx_swt]) + ' = ' + str(str_action))

    def set_fhem_des_temp(self, idx_dev, value):
        """

        :param idx_dev:
        :param value:
        """
        self.send_http_req(self.make_temp_cmd(idx_dev, 'desired-temp', value))
        self.get_cmd_info('FHEM: set desired-temp: ' + self.a_temp_dev[idx_dev] + ' = ' + str(value))

        a_temp_dev_cur = self.a_temp_dev_name[idx_dev]
        self.a_str_value_03[idx_dev] = self.a_str_value_03[idx_dev] + 's'
        self.ev_send_info(idx_dev, a_temp_dev_cur, self.a_str_value_01[idx_dev], self.a_str_value_02[idx_dev],
                      self.a_str_value_03[idx_dev])

    def send_http_req(self, str_cmd, str_type='text'):
        """

        :param str_cmd:
        :param str_type:
        :return:
        """
        resp = requests.get(str_cmd)
        return resp.__getattribute__(str_type)

    def get_fhem_dev_prop(self, idx_dev, b_init = False):
        """

        :param idx_dev:
        """
        bSendinfo = False
        self.str_http_resp = self.send_http_req(self.str_temp_dev_req_tmpl % (
            self.ip_address, self.ip_port, self.a_temp_dev[idx_dev]))

        if idx_dev <= 2:

            d_value_02 = (self.str_split(self.str_http_resp, self.str_actor1 % (
                self.a_temp_dev[idx_dev]), self.str_actor2))
            d_value_03 = float(self.str_split(self.str_http_resp, self.str_des_temp1 % (
                self.a_temp_dev[idx_dev]), self.str_des_temp2))
            d_value_01 = float(self.str_split(self.str_http_resp, self.str_meas_temp1 % (
                self.a_temp_dev[idx_dev]), self.str_meas_temp2))

            a_temp_dev_cur = self.a_temp_dev_name[idx_dev]
            str_val1_cur = 'T ' + str(d_value_01)
            str_val3_cur = 'D ' + str(d_value_03)
            str_val2_cur = 'A ' + str(d_value_02)

        else:
            d_value_01 = float(
                self.str_split(self.str_http_resp, self.str_od_temp1 % (self.a_temp_dev[idx_dev]), self.str_od_temp2))
            d_value_02 = float(
                self.str_split(self.str_http_resp, self.str_od_hum1 % (self.a_temp_dev[idx_dev]), self.str_od_hum2))
            d_value_03 = None

            a_temp_dev_cur = self.a_temp_dev_name[idx_dev]
            str_val1_cur = 'T ' + str(d_value_01)
            str_val2_cur = 'H ' + str(d_value_02)
            str_val3_cur = ''

        if d_value_01 != self.d_value_01[idx_dev]:

            # determine direction
            if b_init:
                self.a_str_value_01[idx_dev] = str_val1_cur
            elif d_value_01 < self.d_value_01[idx_dev]:
                self.a_str_value_01[idx_dev] = str_val1_cur + u'\u2304'
            elif d_value_01 > self.d_value_01[idx_dev]:
                self.a_str_value_01[idx_dev] = str_val1_cur + u'\u2303'
            else:
                self.a_str_value_01[idx_dev] = str_val1_cur

            self.d_value_01[idx_dev] = d_value_01
            bSendinfo = True

        if d_value_02 != self.d_value_02[idx_dev]:

            # determine direction
            if b_init:
                self.a_str_value_02[idx_dev] = str_val2_cur
            elif d_value_02 < self.d_value_02[idx_dev]:
                self.a_str_value_02[idx_dev] =  str_val2_cur + u'\u2304'
            elif d_value_02 > self.d_value_02[idx_dev]:
                self.a_str_value_02[idx_dev] = str_val2_cur + u'\u2303'
            else:
                self.a_str_value_02[idx_dev] = str_val2_cur

            self.d_value_02[idx_dev] = d_value_02
            bSendinfo = True

        if d_value_03 != self.d_value_03[idx_dev]:
            self.a_str_value_03[idx_dev] = str_val3_cur
            self.d_value_03[idx_dev] = d_value_03
            bSendinfo = True

        if bSendinfo:
            self.get_cmd_info('FHEM: ' + a_temp_dev_cur + ' - ' + self.a_str_value_01[idx_dev] + ' - '
                              + self.a_str_value_02[idx_dev] + ' - ' + self.a_str_value_03[idx_dev])
            self.ev_send_info(idx_dev, a_temp_dev_cur, self.a_str_value_01[idx_dev], self.a_str_value_02[idx_dev],
                              self.a_str_value_03[idx_dev])

    def str_split(self, str_base, str_sp1, str_sp2):
        """

        :param str_base:
        :param str_sp1:
        :param str_sp2:
        :return:
        """
        str_base1 = str_base.split(str_sp1)
        str_base2 = str_base1[1].split(str_sp2)
        return str_base2[0]


class EventCall(list):

    def __call__(self, *args, **kwargs):
        for f in self:
            f(*args, **kwargs)

    def __repr__(self):
        return "Event(%s)" % list.__repr__(self)

    def num_ev(self):
        return (len(self))

    def is_linked(self):
        if len(self) > 0:
            return True
        else:
            return False
