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
        req = f"SELECT imei, uuid, timestamp, signal_str, beacon_records.id FROM beacon_records FULL OUTER JOIN beacons ON beacon_records.id = beacons.record WHERE timestamp >= '{checkpoint}';"
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
        for datum in data:
            if datum[0] in self.test_devices or not datum[0]:
                if not results.get(datum[0]):
                    results[datum[0]] = {'all_ts':[]}
                if not results[datum[0]].get(datum[1]):
                    results[datum[0]][datum[1]] = {'timestamps':[], 'signal_str': []}
                results[datum[0]][datum[1]]['timestamps'].append(datum[2])
                results[datum[0]]['all_ts'].append(datum[2])
                if datum[3]:
                    results[datum[0]][datum[1]]['signal_str'].append(datum[3])
        for _, res in results.items():
            all_ts = res['all_ts']
            for _, beac in res.items():

                if type(beac) == dict:
                    beac['missing'] = [ts for ts in all_ts if ts not in beac['timestamps']]
                    beac['visible_pct'] = ((len(all_ts) - len(beac['missing'])) / len(all_ts)) * 100
                    if beac['signal_str']:
                        beac['avg_rssi'] = sum([int(x[:-3]) for x in beac['signal_str']]) / len(beac['signal_str'])
                    else:
                        beac['avg_rssi'] = 0
        return results

    def __query_and_calc(self):
        if self.check_for_devices:
            self.update_test_devices()
        res = self.get_device_data()
        res = self.calc_stats(res)
        if res:
            self.logger.info(self.__pretty_stats(res))
            self.display_info.emit(self.__pretty_stats(res))
            self.checkpoint = datetime.datetime.now()
            self.logger.info(f"Checkpoint is updated to {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
            self.display_info.emit(f"Checkpoint is updated to {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
        else:
            self.logger.warning(f"Couldn't gather statistics. Checkpoint remains at {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
            self.display_info.emit(f"Couldn't gather statistics. Checkpoint remains at {datetime.datetime.strftime(self.checkpoint, self.time_format)}")
        self.timer = threading.Timer(self.check_period, self.__query_and_calc)
        if self.running: self.timer.start()

    def __pretty_stats(self, stats):
        text = f'Periodic ({self.check_period} s.) Beacon Test results:\n\n'
        # import pdb; pdb.set_trace()
        for imei, beac in stats.items():
            text += f"{imei}:\n"
            for uuid, b in beac.items():
                if type(b) == dict:
                    if not uuid: uuid = "Empty"
                    text += f"{uuid}:\n"
                    text += f"Avg. Signal Strength: {b['avg_rssi']} dBm\n"
                    text += f"Visibility: {len(beac['all_ts']) - len(b['missing'])}/{len(beac['all_ts'])}\n"
                    text += f"Percentage %: {b['visible_pct']}\n"
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
        self.timer.cancel()

    def run(self):
        # Creating test and "missing" files for the test.
        open(f'test_{datetime.datetime.strftime(self.start_time, self.file_time_format)}.csv', 'w').close()
        open(f'missing_{datetime.datetime.strftime(self.start_time, self.file_time_format)}.csv', 'w').close()
        self.logger.info(f"Test has been started. Period: {self.check_period}")
        self.display_info.emit(f"Test has been started. Period: {self.check_period}")
        self.running = True
        self.timer.start()
