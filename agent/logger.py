import os

class Logger:
    def __init__(self, filename: str):
        self.filename = filename
        self.logs = []       
        self.all_lines = [] 

        self.idx = 0
        
        if os.path.exists(filename):
            self.load()
        else:
            open(self.filename, 'w', encoding='utf-8').close()

    def add(self, log: str):
        self.logs.append(log)
        self.idx += 1

        self.all_lines.append(log)
        
        self._append_to_file(log)

    def note(self, note: str):
        """增加一条 note，并立即下盘"""
        if not note.startswith('#'):
            formatted_note = '#' + note
        else:
            formatted_note = note
            
        self.all_lines.append(formatted_note)
        
        self._append_to_file(formatted_note)

    def replay(self, idx: int=-1) -> str:
        if idx >= len(self.logs):
            raise IndexError(f"Log index {idx} out of range. Total logs: {len(self.logs)}")

        if idx < 0:
            self.idx += 1
            return self.logs[self.idx-1]

        return self.logs[idx]

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            for line in self.all_lines:
                f.write(line + '\n')

    def load(self):
        self.logs = []
        self.all_lines = []
        self.idx = 0
        
        with open(self.filename, 'r', encoding='utf-8') as f:
            for line in f:
                content = line.rstrip('\n')
                
                self.all_lines.append(content)
                
                if not content.startswith('#'):
                    self.logs.append(content)

    def _append_to_file(self, content: str):
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(content + '\n')

    def __len__(self):
        return len(self.logs)

    def need_replay(self):
        return self.idx < len(self.logs)

if __name__ == "__main__":
    file_path = "persistent_log.txt"
    
    if os.path.exists(file_path):
        os.remove(file_path)

    print("--- 1. 初始化并实时写入 ---")
    logger = Logger(file_path)
    logger.add("第1步：初始化")    # logs[0]
    logger.note("这一个备注")     # 不进 logs
    logger.add("第2步：加载模型")  # logs[1]

    print(f"当前 Log 数: {len(logger.logs)}")
    print(f"当前全量行数: {len(logger.all_lines)}")

    print("\n--- 2. 模拟程序重启 (Load) ---")
    new_logger = Logger(file_path) # 触发 load
    
    print(f"恢复后 Log 数: {len(new_logger.logs)}")  # 应为 2
    print(f"恢复后全量行数: {len(new_logger.all_lines)}") # 应为 3

    print("\n--- 3. 测试 Replay ---")
    print(f"Replay(0): {new_logger.replay(0)}")
    print(f"Replay(1): {new_logger.replay(1)}")
    
    print("\n--- 4. 磁盘文件内容 ---")
    with open(file_path, 'r', encoding='utf-8') as f:
        print(f.read().strip())
