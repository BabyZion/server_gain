import csv
import datetime
import os
import threading
import traceback
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
        self.check_for_devices = True if not test_devices else False
        self.test_devices = test_devices
        self.check_period = check_period
        self.running = False
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
        if data:
            for datum in data:
                for device in self.test_devices:
                    if device in datum:
                        test_data.append(datum)
            data = test_data
            data = sorted(data, key=lambda x:x[4])
            return data
        return None

    def calc_stats(self, data):
        results = {}
        curr_ts = None
        if data:
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
                        beac['all_ts'] = len(all_ts)
                        beac['visible_pct'] = ((beac['all_ts'] - len(beac['missing'])) / beac['all_ts']) * 100
                        if beac['signal_str']:
                            beac['avg_rssi'] = sum([int(x[:-3]) for x in beac['signal_str']]) / len(beac['signal_str'])
                            del beac['signal_str']
                        else:
                            beac['avg_rssi'] = 0
                res['len_ts'] = len(res['all_ts'])
                del res['all_ts']
        return results

    def calc_full_t_len_stats(self, new_d):
        new_data = new_d
        if not self.full_t_len_results:
            # Remove 'missing' list
            # for imei, beac_list in new_data.items():
            #     for beac, beac_data in beac_list.items():
            #         if type(beac_data) == dict:
            #             del beac_data['missing']
            self.full_t_len_results = new_data
        else:
            for imei, beac_list in new_data.items():
                # Adds to len_ts count.
                self.full_t_len_results[imei]['len_ts'] += beac_list['len_ts']
                for beac, beac_data in beac_list.items():
                    
                    if type(beac_data) == dict:
                        if self.full_t_len_results[imei].get(beac):
                            # len_ts
                            old_len_ts = self.full_t_len_results[imei][beac]['all_ts']
                            self.full_t_len_results[imei][beac]['all_ts'] += beac_data['all_ts']
                            # len_missing
                            old_len_missing = self.full_t_len_results[imei][beac]['len_missing']
                            self.full_t_len_results[imei][beac]['len_missing'] += beac_data['len_missing']
                            # visible_pct
                            missing = self.full_t_len_results[imei][beac]['len_missing']
                            all_ts = self.full_t_len_results[imei][beac]['all_ts']
                            self.full_t_len_results[imei][beac]['visible_pct'] = ((all_ts - missing)/all_ts) * 100
                            # avg_rssi
                            b = self.full_t_len_results[imei][beac]['avg_rssi']
                            a = old_len_ts - old_len_missing
                            a1 = self.full_t_len_results[imei][beac]['all_ts'] - self.full_t_len_results[imei][beac]['len_missing']
                            b1 = beac_data['avg_rssi'] 
                            self.full_t_len_results[imei][beac]['avg_rssi'] = (b*a + b1*a1)/(a + a1)
                        else:
                            self.full_t_len_results[imei][beac] = {}
                            self.full_t_len_results[imei][beac]['all_ts'] = beac_data['all_ts']
                            self.full_t_len_results[imei][beac]['len_missing'] = beac_data['len_missing']
                            self.full_t_len_results[imei][beac]['visible_pct'] = beac_data['visible_pct']
                            self.full_t_len_results[imei][beac]['avg_rssi'] = beac_data['avg_rssi']
                # Increase 'all_ts' of remaining beacons that have already been visible but not during this period
                for beacon in self.full_t_len_results[imei]:
                    if beacon not in beac_list:
                       self.full_t_len_results[imei][beacon]['all_ts'] += beac_list['len_ts']
                       self.full_t_len_results[imei][beacon]['len_missing'] += beac_list['len_ts']
                    
    def write_results_to_files(self, periodic_stats, full_stats):
        try:
            for imei, beac_list in periodic_stats.items():
                for beac, data in beac_list.items():
                    try:
                        for m in data['missing']:
                            mis = {'imei':imei, 'beacon':beac, 'date':datetime.datetime.strftime(m, self.time_format)}
                            with open(self.test_missing_file, 'a') as mf:
                                writer = csv.DictWriter(mf, fieldnames=mis.keys())
                                if os.stat(self.test_missing_file).st_size == 0:
                                    writer.writeheader()
                                writer.writerow(mis)
                    except TypeError:
                        pass
                    if type(data) == dict:
                        del data['missing']
                        data['imei'] = imei
                        data['beacon'] = beac
                        data['stats'] = 'periodic'
                        with open(self.test_res_file, 'a') as f:
                            writer = csv.DictWriter(f, fieldnames=data.keys())
                            if os.stat(self.test_res_file).st_size == 0:
                                writer.writeheader()
                            writer.writerow(data)
            for imei, beac_list in full_stats.items():        
                for beac, data in beac_list.items():
                    if type(data) == dict:
                        data['imei'] = imei
                        data['beacon'] = beac
                        data['stats'] = 'full'
                        with open(self.test_res_file, 'a') as f:
                            writer = csv.DictWriter(f, fieldnames=data.keys())
                            writer.writerow(data)
            self.logger.info("Results are written to csv file.")
            self.display_info.emit("Results are written to csv file.")
        except PermissionError as e:
            self.logger.info("Results of this period couldn't be written to file - {e}")
            self.display_info.emit("Results of this period couldn't be written to file - {e}")

    def __query_and_calc(self):
        try:
            if self.check_for_devices:
                self.update_test_devices()
            res = self.get_device_data()
            res = self.calc_stats(res)
            if res:
                self.logger.info(self.__pretty_stats(res))
                self.display_info.emit(self.__pretty_stats(res))
                self.checkpoint = datetime.datetime.now()
                self.calc_full_t_len_stats(res)
                self.write_results_to_files(res, self.full_t_len_results)
                self.logger.info(f"Checkpoint is updated to {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
                self.display_info.emit(f"Checkpoint is updated to {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
                self.logger.info(self.__pretty_stats(self.full_t_len_results, 'Full'))
                self.display_info.emit(self.__pretty_stats(self.full_t_len_results, 'Full'))
            else:
                self.logger.warning(f"Couldn't gather statistics. Checkpoint remains at {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
                self.display_info.emit(f"Couldn't gather statistics. Checkpoint remains at {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
            self.timer = threading.Timer(self.check_period, self.__query_and_calc)
            if self.running: self.timer.start()
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def __pretty_stats(self, stats, res_type='Periodic'):
        try:
            text = f'{res_type} ({self.check_period} s.) Beacon Test results:\n\n'
            # import pdb; pdb.set_trace()
            for imei, beac in stats.items():
                text += f"{imei}:\n"
                for uuid, b in beac.items():
                    if type(b) == dict:
                        if not uuid: uuid = "Empty"
                        text += f"{uuid}:\n"
                        text += f"Avg. Signal Strength: {b['avg_rssi']} dBm\n"
                        text += f"Visibility: {b['all_ts'] - b['len_missing']}/{b['all_ts']}\n"
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
        except KeyError:
            self.logger.error(traceback.format_exc())

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.cancel()

    def run(self):
        self.full_t_len_results = None
        self.checkpoint = datetime.datetime.now()
        self.start_time = datetime.datetime.now()
        # Creating test and "missing" files for the test.
        self.test_res_file = f'test_{datetime.datetime.strftime(self.start_time, self.file_time_format)}.csv'
        self.test_missing_file = f'missing_{datetime.datetime.strftime(self.start_time, self.file_time_format)}.csv'
        open(self.test_res_file, 'w').close()
        open(self.test_missing_file, 'w').close()
        self.logger.info(f"Test has been started. Period: {self.check_period}")
        self.display_info.emit(f"Test has been started. Period: {self.check_period}")
        self.running = True
        self.timer = threading.Timer(self.check_period, self.__query_and_calc)
        self.timer.start()