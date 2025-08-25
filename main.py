import Dataloader, Painter

if __name__ == '__main__':
    dataloader = Dataloader.TrainDataLoader(res_path = r".\TimeTable")
    segments = dataloader.load()

    stations = []
    with open(r".\TimeTable\Stations.ini", "r", encoding="utf-8") as f:
        # 逐行阅读，并添加进列表当中
        for line in f.readlines():
            stations.append(line.strip())

    print(stations)
    print(segments)

    painter = Painter.Painter(station_order = stations,train_data = segments)
    painter.draw()