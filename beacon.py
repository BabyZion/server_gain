import datetime
import threading
from logger import Logger
from PyQt5 import QtCore


class Beacon(QtCore.QThread):

    display_info = QtCore.pyqtSignal(str)

    def __init__(self, database, test_devices=None, check_period=None):
        super().__init__()
        self.time_format = '%Y.%m.%d %H:%M:%S.%f'
        self.file_time_format = '%Y_%m_%d-%H_%M_%S'
        self.db = database
        # self.checkpoint = datetime.datetime.strftime(datetime.datetime.now(), self.time_format)
        self.checkpoint = datetime.datetime.now()
        self.start_time = datetime.datetime.now()
        self.check_for_devices = True if not test_devices else False
        self.test_devices = test_devices
        self.check_period = check_period
        self.full_t_len_results = None
        self.running = False
        self.timer = threading.Timer(self.check_period, self.__query_and_calc)
        self.logger = Logger('Beacon Test')

        
    def update_test_devices(self):
        # req = f"SELECT DISTINCT imei FROM beacons WHERE timestamp > '{self.start_time}';"
        checkpoint = datetime.datetime.strftime(self.checkpoint, self.time_format)
        req = f"SELECT DISTINCT imei FROM beacon_records WHERE timestamp >= '{checkpoint}';"
        imeis = self.db.request(req)
        if imeis:
            self.test_devices = []
            for i in imeis:
                if i[0]:
                    self.test_devices.append(i[0])
            self.logger.info(f"Successfully updated participating device list.")
            self.display_info.emit(f"Successfully updated participating device list.")
        else:
            self.logger.error(f"Couldn't update participating device list.")
            self.display_info.emit(f"Couldn't update participating device list.")

    def get_device_data(self):
        checkpoint = datetime.datetime.strftime(self.checkpoint, self.time_format)
        req = f"SELECT imei, uuid, timestamp, signal_str, beacon_records.id FROM beacon_records FULL OUTER JOIN beacons ON beacon_records.id = beacons.record WHERE timestamp >= '{checkpoint}' ORDER BY timestamp;"
        data = self.db.request(req)
        test_data = []
        for datum in data:
            for device in self.test_devices:
                if device in datum:
                    test_data.append(datum)
        data = test_data
        data = sorted(data, key=lambda x:x[4])
        return data

    def calc_stats(self, data):
        results = {}
        curr_ts = None
        for datum in data:
            if datum[0] in self.test_devices or not datum[0]:
                if not results.get(datum[0]):
                    results[datum[0]] = {'all_ts':[]}
                if not results[datum[0]].get(datum[1]):
                    results[datum[0]][datum[1]] = {'timestamps':[], 'signal_str': []}
                results[datum[0]][datum[1]]['timestamps'].append(datum[2])
                if curr_ts != datum[2] or not curr_ts:
                    results[datum[0]]['all_ts'].append(datum[2])
                    curr_ts = datum[2]
                if datum[3]:
                    results[datum[0]][datum[1]]['signal_str'].append(datum[3])
        for _, res in results.items():
            all_ts = res['all_ts']
            for _, beac in res.items():

                if type(beac) == dict:
                    beac['missing'] = [ts for ts in all_ts if ts not in beac['timestamps']]
                    del beac['timestamps']
                    beac['len_missing'] = len(beac['missing'])
                    beac['visible_pct'] = ((len(all_ts) - len(beac['missing'])) / len(all_ts)) * 100
                    if beac['signal_str']:
                        beac['avg_rssi'] = sum([int(x[:-3]) for x in beac['signal_str']]) / len(beac['signal_str'])
                        del beac['signal_str']
                    else:
                        beac['avg_rssi'] = 0
            res['len_ts'] = len(res['all_ts'])
            del res['all_ts']
        return results

    def calc_full_t_len_stats(self, new_data):
        # new_data = self.__prep_data_for_full_len_calculation(new_data)
        if not self.full_t_len_results:
            # Remove 'missing' list
            for imei, beac_list in new_data.items():
                for beac, beac_data in beac_list.items():
                    if type(beac_data) == dict:
                        del beac_data['missing']
            self.full_t_len_results = new_data
        else:
            for imei, beac_list in new_data.items():
                # Adds to len_ts count.
                old_len_ts = self.full_t_len_results[imei]['len_ts']
                self.full_t_len_results[imei]['len_ts'] += beac_list['len_ts']
                for beac, beac_data in beac_list.items():
                    
                    if type(beac_data) == dict:
                        # len_missing
                        old_len_missing = self.full_t_len_results[imei][beac]['len_missing']
                        self.full_t_len_results[imei][beac]['len_missing'] += beac_data['len_missing']
                        # visible_pct
                        missing = self.full_t_len_results[imei][beac]['len_missing']
                        all_ts = self.full_t_len_results[imei]['len_ts']
                        self.full_t_len_results[imei][beac]['visible_pct'] = ((all_ts - missing)/all_ts) * 100
                        # avg_rssi
                        b = self.full_t_len_results[imei][beac]['avg_rssi']
                        a = old_len_ts - old_len_missing
                        a1 = self.full_t_len_results[imei]['len_ts'] - self.full_t_len_results[imei][beac]['len_missing']
                        b1 = beac_data['avg_rssi'] 
                        self.full_t_len_results[imei][beac]['avg_rssi'] = (b*a + b1*a1)/(a + a1)
        # print(self.full_t_len_results)
        # print('------------------------------------------------------------------')
        # print(self.__pretty_stats(self.full_t_len_results, 'Full'))

    # def __prep_data_for_full_len_calculation(self, data):
    #     print(data)
    #     print()
    #     for _, res in data.items():
    #         res['len_all_ts'] = len(res['all_ts'])
    #         del res['all_ts']
    #         for _, beac in res.items():
    #             if type(beac) == dict:
    #                 beac['len_all_missing'] = len(beac['missing'])
    #     return data

    def __query_and_calc(self):
        if self.check_for_devices:
            self.update_test_devices()
        res = self.get_device_data()
        res = self.calc_stats(res)
        if res:
            self.logger.info(self.__pretty_stats(res))
            self.display_info.emit(self.__pretty_stats(res))
            self.checkpoint = datetime.datetime.now()
            self.calc_full_t_len_stats(res)
            self.logger.info(f"Checkpoint is updated to {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
            self.display_info.emit(f"Checkpoint is updated to {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
            self.logger.info(self.__pretty_stats(self.full_t_len_results, 'Full'))
            self.display_info.emit(self.__pretty_stats(self.full_t_len_results, 'Full'))
        else:
            self.logger.warning(f"Couldn't gather statistics. Checkpoint remains at {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
            self.display_info.emit(f"Couldn't gather statistics. Checkpoint remains at {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
        self.timer = threading.Timer(self.check_period, self.__query_and_calc)
        if self.running: self.timer.start()

    def __pretty_stats(self, stats, res_type='Periodic'):
        text = f'{res_type} ({self.check_period} s.) Beacon Test results:\n\n'
        # import pdb; pdb.set_trace()
        for imei, beac in stats.items():
            text += f"{imei}:\n"
            for uuid, b in beac.items():
                if type(b) == dict:
                    if not uuid: uuid = "Empty"
                    text += f"{uuid}:\n"
                    text += f"Avg. Signal Strength: {b['avg_rssi']} dBm\n"
                    text += f"Visibility: {beac['len_ts'] - b['len_missing']}/{beac['len_ts']}\n"
                    text += f"Percentage %: {b['visible_pct']}\n"
                    if b.get('missing'):
                        text += "Missing:\n"
                        if b['missing']:
                            try:
                                for i in range(5):
                                    text += f"{datetime.datetime.strftime(b['missing'][i], self.time_format)}\n"
                            except IndexError:
                                pass
                            text += "...\n"
                        else:
                            text += "None\n"
                text += '\n'
        return text

    def stop(self):
        self.running = False
        self.full_t_len_results = None
        self.timer.cancel()

    def run(self):
        # Creating test and "missing" files for the test.
        open(f'test_{datetime.datetime.strftime(self.start_time, self.file_time_format)}.csv', 'w').close()
        open(f'missing_{datetime.datetime.strftime(self.start_time, self.file_time_format)}.csv', 'w').close()
        self.logger.info(f"Test has been started. Period: {self.check_period}")
        self.display_info.emit(f"Test has been started. Period: {self.check_period}")
        self.running = True
        self.timer.start()
