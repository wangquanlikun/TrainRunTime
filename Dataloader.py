import os
from collections import defaultdict

class TrainDataLoader:
    def __init__(self, res_path):
        self.path = res_path

    def load(self):
        # 读取每个站点信息，返回每辆车信息的列表
        # 存储所有车次的时刻表信息: {车次号: [(站名, 到达时间, 发车时间), ...]}
        train_schedules = defaultdict(list)

        # 遍历目录下的所有.txt文件
        if not os.path.exists(self.path):
            return []

        for filename in os.listdir(self.path):
            if filename.endswith('.txt'):
                station_name = filename[:-4]  # 去掉.txt后缀作为站名
                filepath = os.path.join(self.path, filename)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue

                            parts = line.split()
                            if len(parts) >= 3:
                                train_no = parts[0]
                                arrival_time = parts[1]
                                departure_time = parts[2]

                                train_schedules[train_no].append((station_name, arrival_time, departure_time))
                except Exception as e:
                    print(f"读取文件 {filepath} 时出错: {e}")
                    continue

        # 生成segments列表
        segments = []

        for train_no, schedule in train_schedules.items():
            # 按时间排序站点（使用到达时间排序）
            schedule.sort(key=lambda x: x[1])

            for i, (station, arrival, departure) in enumerate(schedule):
                # 添加停站段（到达时间 -> 发车时间，同一站点）
                if arrival != "--:--" and departure != "--:--":
                    segments.append((arrival, departure, station, station, "Null", train_no))

                # 添加运行段（当前站发车 -> 下一站到达，不同站点）
                if i < len(schedule) - 1:
                    next_station, next_arrival, _ = schedule[i + 1]
                    segments.append((departure, next_arrival, station, next_station, "Null", train_no))

        return segments
