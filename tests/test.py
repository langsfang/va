import subprocess
import json
import sys
from pathlib import Path

def run_test(binary_path, input_file, reference_file):
    """
    运行测试并对比 score
    """
    try:
        # 1. 运行程序: ./my_program <input_file_path>
        # capture_output=True 捕获 stdout 和 stderr
        result = subprocess.run(
            [str(binary_path), str(input_file)], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # 2. 从 stdout 解析程序输出的 JSON 字符串
        try:
            output_json = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return None, None, f"Failed to parse JSON from stdout: {result.stdout[:100]}..."

        current_score = float(output_json.get("playerCurHp", 0))

        # 3. 解析参考输出文件
        with open(reference_file, 'r') as f_ref:
            ref_json = json.load(f_ref)
            ref_score = float(ref_json.get("playerCurHp", 0))

        return current_score, ref_score, None

    except subprocess.CalledProcessError as e:
        return None, None, f"Binary exited with error: {e.stderr}"
    except Exception as e:
        return None, None, str(e)

def main():
    # --- 配置区 ---
    test_root = Path("./tests")         # 测试用例所在的根目录
    binary_path = Path("./3rd/sts_lightspeed/build/battle-agent").absolute()  # 二进制程序的路径
    input_name = "input.json"           # 输入文件名
    ref_name = "ref.json"               # 参考输出文件名
    # --------------

    if not binary_path.exists():
        print(f"Error: Binary not found at {binary_path}")
        sys.exit(1)

    # 统计数据结构
    stats = {
        "total": 0,
        "passed": 0,        # 完全一致
        "regressions": [],  # score 变小
        "improvements": [], # score 变大
        "errors": []        # 运行报错
    }

    print(f"{'Case Directory':<25} | {'Current':<10} | {'Ref':<10} | {'Status'}")
    print("-" * 75)

    # 遍历目录
    for case_dir in test_root.iterdir():
        if not case_dir.is_dir():
            continue
            
        input_file = case_dir / input_name
        ref_file = case_dir / ref_name

        # 只有两个文件都存在才执行测试
        if input_file.exists() and ref_file.exists():
            stats["total"] += 1
            
            curr, ref, err = run_test(binary_path, input_file, ref_file)

            if err:
                print(f"{case_dir.name:<25} | {'ERROR':<10} | {'-':<10} | {err}")
                stats["errors"].append((case_dir.name, err))
                continue

            if curr < ref:
                status = "REGRESSION ↓"
                stats["regressions"].append((case_dir.name, curr, ref))
            elif curr > ref:
                status = "IMPROVED ↑"
                stats["improvements"].append((case_dir.name, curr, ref))
            else:
                status = "STABLE"
                stats["passed"] += 1

            print(f"{case_dir.name:<25} | {curr:<10.2f} | {ref:<10.2f} | {status}")

    # --- 最终统计报表 ---
    print("\n" + "="*45)
    print(f"{'TEST SUMMARY':^45}")
    print("="*45)
    print(f"Total Folders:  {stats['total']}")
    print(f"Stable (Match): {stats['passed']}")
    print(f"Improvements:   {len(stats['improvements'])}  (Great!)")
    print(f"Regressions:    {len(stats['regressions'])}  (Fix needed)")
    print(f"Errors:         {len(stats['errors'])}")
    print("="*45)

    if stats["improvements"]:
        print("\n📈 Improvements Detail:")
        for name, c, r in stats["improvements"]:
            print(f"  + {name}: {r} -> {c} (+{c-r:.2f})")

    if stats["regressions"]:
        print("\n📉 Regression Detail:")
        for name, c, r in stats["regressions"]:
            print(f"  - {name}: {r} -> {c} ({c-r:.2f})")

    # 如果有回归或错误，返回非零退出码（CI 友好）
    if stats["regressions"] or stats["errors"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
