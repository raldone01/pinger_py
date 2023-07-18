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
from datetime import datetime
from matplotlib.dates import DateFormatter, date2num, num2date
from matplotlib.ticker import MaxNLocator, FuncFormatter
import matplotlib
import signal

matplotlib.use('Qt5Agg')


class Pinger(QtCore.QObject):
    newDataSignal = QtCore.Signal(list)

    def __init__(self, server, interval=30, csv_file=None):
        super().__init__()
        self.server = server
        self.ip = gethostbyname(self.server)
        self.interval = interval
        self.csv_file = csv_file
        self.ping_results = []
        self.running = True

    @QtCore.Slot()
    def start(self):
        while self.running:
            timestamp = datetime.now()  # Use Python datetime here
            try:
                response_time = ping(self.server)
                success = 1 if response_time else 0
            except Exception:
                response_time = None
                success = 0

            response_time_ms = None if response_time is None else round(response_time * 1000)
            # convert timestamp to unix
            timestamp = timestamp.timestamp()
            result = (timestamp, self.ip, success, response_time_ms)
            print(f"{timestamp};{self.ip};{success};{response_time_ms}")
            self.ping_results.append(result)

            if self.csv_file:
                with open(self.csv_file, 'a', newline='') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(result)

            time.sleep(self.interval)

            self.newDataSignal.emit(self.ping_results)

    def stop(self):
        self.running = False


class MyMplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

    def update_figure(self, ping_results):
        self.axes.clear()
        self.axes.grid(True)

        timestamps, _, successes, response_times = zip(*ping_results)
        timestamps = [date2num(t) for t in timestamps]  # Convert datetime to Matplotlib's internal representation

        def format_func(x, pos):
            dt = num2date(x)
            if max(timestamps) - min(timestamps) <= 60:
                return dt.strftime('%H:%M:%S')
            else:
                return dt.strftime('%H:%M')

        self.axes.xaxis.set_major_locator(MaxNLocator(10))
        self.axes.xaxis.set_major_formatter(FuncFormatter(format_func))

        for t, s in zip(timestamps, successes):
            if s == 0:
                self.axes.axvline(x=t, color='r', linewidth=2)
        self.axes.plot(timestamps, response_times, 'b')
        self.draw()


def main():
    parser = argparse.ArgumentParser(description='Ping a server periodically and plot the response time.')
    parser.add_argument('server', type=str, help='The server to ping.')
    parser.add_argument('-n', type=int, default=30, help='The interval between pings in seconds.')
    parser.add_argument('--csv', type=str, help='The CSV file to write results to.')
    parser.add_argument('--headless', action='store_true', help='Run without a GUI.')
    args = parser.parse_args()

    app = QApplication([])
    app.setApplicationDisplayName("Server Pinger")

    pinger = Pinger(args.server, args.n, args.csv)
    pinger_thread = QtCore.QThread()
    pinger.moveToThread(pinger_thread)
    pinger_thread.started.connect(pinger.start)
    pinger_thread.start()

    timer = QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    if not args.headless:
        sc = MyMplCanvas()
        pinger.newDataSignal.connect(sc.update_figure)
        sc.show()
    else:
        app.setQuitOnLastWindowClosed(False)

    def on_quit(*args):
        app.quit()
        pinger.stop()
        pinger_thread.quit()
        pinger_thread.wait()
    signal.signal(signal.SIGINT, on_quit)
    app.exec()

    print("event loop finished")

    on_quit()


if __name__ == "__main__":
    main()
