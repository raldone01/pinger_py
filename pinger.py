import argparse
import csv
import time
from ping3 import ping
from PySide6 import QtCore
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from socket import gethostbyname
from datetime import datetime, timedelta
from matplotlib.dates import DateFormatter, date2num, num2date
from matplotlib.ticker import MaxNLocator, FuncFormatter
import matplotlib
import signal

matplotlib.use('Qt5Agg')


class Pinger(QtCore.QObject):
    newDataSignal = QtCore.Signal(list)

    def __init__(self, server, interval=30, csv_file=None, recall=False):
        super().__init__()
        self.server = server
        self.ip = gethostbyname(self.server) if self.server else None
        self.interval = interval
        self.csv_file = csv_file
        self.ping_results = []
        self.recall = recall
        self.running = True

        if self.recall:
            self.recall_results()

    def stoppable_sleep(self, ms):
        max_wait = 100
        while ms > 0 and self.running:
            time.sleep(min(ms, max_wait) / 1000)
            ms -= max_wait

    @QtCore.Slot()
    def start(self):
        if self.recall:
            self.newDataSignal.emit(self.ping_results)

        if self.server is None:
            return
        while self.running:
            timestamp = datetime.now()  # Use Python datetime here
            try:
                response_time = ping(self.server)
                success = 1 if response_time else 0
            except Exception:
                response_time = None
                success = 0

            response_time_ms = None if response_time is None else round(response_time * 1000)
            result = (timestamp.timestamp(), self.ip, success, response_time_ms)
            print(f"{timestamp};{self.ip};{success};{response_time_ms}")
            self.ping_results.append(result)

            if self.csv_file:
                with open(self.csv_file, 'a', newline='') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(result)
            self.newDataSignal.emit(self.ping_results)

            self.stoppable_sleep(self.interval * 1000)


    def recall_results(self):
        with open(self.csv_file, 'r', newline='') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                timestamp = float(row[0])
                result = (timestamp, row[1], int(row[2]), int(row[3]))
                self.ping_results.append(result)
                print(f"{datetime.fromtimestamp(timestamp)};{row[1]};{row[2]};{row[3]}")

    def stop(self):
        self.running = False


class MyMplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_ylabel('Response Time (Milliseconds)')
        self.axes.set_xlabel('Time')
        self.axes.grid(True)
        self.axes.set_title('Server Pinger')
        self.fig.tight_layout()
        self.hl, = self.axes.plot([], [], 'b')
        super().__init__(self.fig)

    def update_figure(self, ping_results):
        if not ping_results:
            return

        timestamps, ips, successes, response_times = zip(*ping_results)
        timestamps = [datetime.fromtimestamp(t) for t in timestamps]  # Convert datetime to Matplotlib's internal representation

        self.axes.set_title(f"{ips[0]} - {timestamps[0]}")

        def format_func(x, pos):
            dt = num2date(x)
            if max(timestamps) - min(timestamps) <= timedelta(seconds=60):
                return dt.strftime('%H:%M:%S')
            else:
                return dt.strftime('%H:%M')

        self.axes.xaxis.set_major_locator(MaxNLocator(10))
        self.axes.xaxis.set_major_formatter(FuncFormatter(format_func))

        # mark failed pings with red zones
        # pings are not equally spaced compute the span to the next ping
        global app_args
        for i in range(len(successes)):
            if successes[i] == 0:
                start = timestamps[i]
                end = timestamps[i+1] if i < len(successes) - 1 else timestamps[i] + timedelta(seconds=app_args.n)
                self.axes.axvspan(start, end, alpha=0.2, color='red')

        self.hl.set_data(date2num(timestamps), response_times)
        self.axes.relim()
        self.axes.autoscale_view()

        self.draw()

app_args = None

def main():
    parser = argparse.ArgumentParser(description='Ping a server periodically and plot the response time.')
    parser.add_argument('server', type=str, nargs='?', default=None, help='The server to ping.')
    parser.add_argument('--recall', action='store_true', help='Recall recorded results.')
    parser.add_argument('-n', type=int, default=30, help='The interval between pings in seconds.')
    parser.add_argument('--csv', type=str, help='The CSV file to write results to.')
    parser.add_argument('--headless', action='store_true', help='Run without a GUI.')
    args = parser.parse_args()
    global app_args
    app_args = args

    app = QApplication([])
    app.setApplicationDisplayName("Server Pinger")

    pinger = Pinger(args.server, args.n, args.csv, args.recall)
    pinger_thread = QtCore.QThread()
    pinger.moveToThread(pinger_thread)

    timer = QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    if not args.headless:
        sc = MyMplCanvas()
        pinger.newDataSignal.connect(sc.update_figure)
        sc.show()
    else:
        app.setQuitOnLastWindowClosed(False)

    pinger_thread.started.connect(pinger.start)
    pinger_thread.start()

    def on_quit(*args):
        app.quit()
        pinger.stop()
        pinger_thread.quit()
        pinger_thread.wait()
    signal.signal(signal.SIGINT, on_quit)
    app.exec()
    on_quit()

if __name__ == "__main__":
    main()
