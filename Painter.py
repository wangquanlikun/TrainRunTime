import matplotlib as mpl
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt
import mplcursors
import datetime as dt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors

class Painter:
    def __init__(self, station_order = None, train_data = None):
        self.stations = station_order

        self.segments = Painter.assign_colors_to_segments(train_data) if train_data is not None else []
        # 每条线段格式： (start_time, end_time, y_start_label, y_end_label, color, info)
        # 时间用 'HH:MM' 字符串

        # 注册使用的中文字体
        font_path = r"C:\Windows\Fonts\simhei.ttf"
        fm.fontManager.addfont(font_path)
        self.prop = fm.FontProperties(fname=font_path)
        font_name = self.prop.get_name()
        mpl.rcParams['font.family'] = 'sans-serif'
        mpl.rcParams['font.sans-serif'] = [font_name]
        mpl.rcParams['axes.unicode_minus'] = False

    @staticmethod
    def assign_colors_to_segments(segments, cmap_name='tab20'):
        """
        为 segments 分配颜色：相同 info -> 相同颜色，不同 info -> 不同颜色。
        支持 segments 中每项为 tuple/list（默认 info 在最后一位、color 在倒数第二位）
        或 dict（需要包含 'info' 键，可包含/更新 'color' 键）。

        返回：新的 segments 列表（保持原有顺序、类型对 dict 返回新 dict，对 tuple 返回 tuple）
        颜色为 hex 字符串 '#RRGGBB'，可直接用于 matplotlib。
        """
        # 1) 收集按出现顺序的唯一 info
        infos = []
        for seg in segments:
            if isinstance(seg, dict):
                info = seg.get('info')
            else:
                # 列表/元组：默认 info 在最后一位
                info = seg[-1]
            if info not in infos:
                infos.append(info)

        n = len(infos)
        if n == 0:
            return list(segments)  # 没有 segments，直接返回

        # 2) 生成 n 个互异颜色（优先用 tab20，当 n > 20 用 HSV 均匀采样）
        if n <= 20:
            cmap = plt.get_cmap(cmap_name)
            # 均匀采样（当 n==1 时避免除零）
            colors = [mcolors.to_hex(cmap(i / max(1, n - 1))) for i in range(n)]
        else:
            # 使用 HSV 均匀分布，确保任意 n 都能生成
            colors = [mcolors.to_hex(plt.cm.get_cmap('hsv')(i / n)) for i in range(n)]

        info2color = {info: colors[i] for i, info in enumerate(infos)}

        # 3) 根据原始类型构建返回的 segments（更新 color 字段/位置）
        new_segments = []
        for seg in segments:
            if isinstance(seg, dict):
                new_seg = dict(seg)  # 复制一份，避免改动原对象
                info = new_seg.get('info')
                new_seg['color'] = info2color.get(info)
                new_segments.append(new_seg)
            else:
                # tuple / list 情况：我们默认 info 在最后一位，color 在倒数第二位
                seq = list(seg)
                if len(seq) >= 2:
                    info = seq[-1]
                    seq[-2] = info2color.get(info)  # 覆盖 color 字段
                    new_segments.append(tuple(seq))
                else:
                    # 不符合预期的短序列，直接返回原样（不修改）
                    new_segments.append(tuple(seq))

        return new_segments

    def draw(self):
        all_labels = []
        for s in self.segments:
            a, b = s[2], s[3]
            if a not in all_labels:
                all_labels.append(a)
            if b not in all_labels:
                all_labels.append(b)

        if self.stations:
            ordered = [lab for lab in self.stations if lab in all_labels]
            ordered += [lab for lab in all_labels if lab not in ordered]
            y_labels = ordered
        else:
            y_labels = all_labels

        y_positions = {label: i for i, label in enumerate(y_labels)}

        today = dt.date.today()
        def str_to_dt(tstr):
            if isinstance(tstr, str):
                t = dt.datetime.strptime(tstr, "%H:%M").time()
                return dt.datetime.combine(today, t)
            elif isinstance(tstr, dt.datetime):
                return tstr
            elif isinstance(tstr, dt.time):
                return dt.datetime.combine(today, tstr)
            else:
                raise ValueError("时间必须是 'HH:MM' 字符串或 datetime/time 对象")

        fig, ax = plt.subplots(figsize=(12, 4.5))

        lines = []
        for start_s, end_s, y_start_label, y_end_label, color, info in self.segments:
            x0 = str_to_dt(start_s)
            x1 = str_to_dt(end_s)
            y0 = y_positions[y_start_label]
            y1 = y_positions[y_end_label]
            # 绘制线段（粗线，capstyle='butt' 保持线段在端点处方正）
            line, = ax.plot([x0, x1], [y0, y1], linewidth=3, solid_capstyle='butt',
                            color=color, picker=6)  # picker=像素容差
            # 绑定信息（用于点击回调）
            line._info = info
            line._label = f"{y_start_label} → {y_end_label}  {start_s}-{end_s}"
            lines.append(line)
            # 可选：在起止点绘制小端点以增强可视化
            ax.scatter([x0, x1], [y0, y1], s=8, marker='o', edgecolors='k', linewidths=0.1, color=color, zorder=3)

        # 设置纵轴刻度与标签（使用中文字体 prop 确保中文正常显示）
        ax.set_yticks(list(y_positions.values()))
        if self.prop is not None:
            ax.set_yticklabels(y_labels, fontproperties=self.prop)
        else:
            ax.set_yticklabels(y_labels)

        # x 轴时间格式化
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=10)

        ax.set_xlabel("时间（HH:MM）", fontproperties=self.prop if self.prop is not None else None)
        ax.set_title("列车运行图",
                     fontproperties=self.prop if self.prop is not None else None)

        # 网格与范围调整
        ax.grid(axis='x', linestyle='--', alpha=0.5)
        ax.set_ylim(-0.5, len(y_labels) - 0.5)
        ax.set_xlim(min(str_to_dt(s[0]) for s in self.segments) - dt.timedelta(minutes=10),
                    max(str_to_dt(s[1]) for s in self.segments) + dt.timedelta(minutes=10))


        cursor = mplcursors.cursor(lines, hover=False)
        @cursor.connect("add")
        def on_add(sel):
            artist = sel.artist
            info = getattr(artist, "_info", "无信息")
            label = getattr(artist, "_label", "")
            sel.annotation.set_text(f"{label}\n{info}")
            if self.prop is not None:
                sel.annotation.set_fontproperties(self.prop)
            sel.annotation.get_bbox_patch().set(alpha=0.9)

        plt.tight_layout()
        plt.show()

if __name__ == '__main__':
    # TEST
    segments = [
        ("10:47", "10:56", "成都东", "成都东", "Null", "G308"),
        ("10:56", "11:20", "成都东", "德阳", "Null", "G308"),
        ("11:20", "11:22", "德阳", "德阳", "Null", "G308"),
        ("11:22", "11:39", "德阳", "绵阳", "Null", "G308"),
    ]
    painter = Painter(train_data = segments)
    painter.draw()