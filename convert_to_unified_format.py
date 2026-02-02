# -*- coding: utf-8 -*-
"""
将所有xlsx文件转换为统一格式的脚本
每个sheet对应一个剧情ID（剧情ID从sheet名称读取，sheet名称应为纯数字，如"80002"）
"""
import pandas as pd
import os
import glob
import re
from collections import OrderedDict

class XlsxConverter:
    """
    将xlsx文件转换为统一格式
    每个sheet对应一个剧情ID（从sheet名称读取，sheet名称应为纯数字）
    """
    
    def __init__(self):
        """初始化转换器"""
        # 剧情ID从sheet名称读取（sheet名称应为纯数字，如"80002"）
        self.event_id = 20000  # 事件ID起始值
        self.content_id = 20000  # 对话内容ID起始值
        self.option_id = 2000  # 选项ID起始值
        
        self.plot_data = []  # 剧情表数据
        self.event_data = []  # 事件表数据
        self.content_data = []  # 对话表数据
        self.option_data = []  # 选项表数据
        
        # 文件名到剧情ID的映射，用于处理选项的跳转
        self.file_sheet_to_plot_id = {}  # {(filename, sheetname): plot_id}
        # 选项到文件名的映射
        self.option_to_file = {}  # {option_id: (filename, branches_str)}
        
        # 列索引映射（基于表头行）
        self.col_indices = {
            'role': 0,       # 角色
            'text': 1,       # 文本内容
            'event': 18,     # 事件
            'music': 19,     # 音乐
            'audio': 20,     # 音效
            'voice': 21,     # 语音
            'animation': 22, # 角色动画
            'action': 23,    # 具体动作
            'painting': 24,  # 立绘
            'bgAnim': 25,    # 场景动画
            'bg': 26,        # 背景
            'props': 27,     # 特殊道具图
            'jump': 28,      # 跳转界面
            'options': 29,   # 跳转选项
            'branches': 30,  # 跳转分支
            'dialog': 31,    # 对话框
            'nobacktracking': 32,  # 不重复回溯
            'ending': 33,     # 特定结局
            'jumpStory': 34,  # 跳转剧情
            'specialOption': 35  # 特殊选项
        }
    
    def process_file(self, filename):
        """
        处理单个xlsx文件，每个sheet对应一个剧情ID（从sheet名称读取）
        
        参数:
            filename: 文件路径
        """
        try:
            print(f"\n处理文件: {os.path.basename(filename)}")
            excel_file = pd.ExcelFile(filename)
            
            # 处理文件中的所有sheet
            for sheet_name in excel_file.sheet_names:
                self.process_sheet(excel_file, sheet_name, filename)
                
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def process_sheet(self, excel_file, sheet_name, filename):
        """
        处理单个工作表，每个sheet生成一个剧情
        
        参数:
            excel_file: Excel文件对象
            sheet_name: 工作表名称（应为纯数字，作为剧情ID）
            filename: 文件名
        """
        try:
            print(f"  处理工作表: {sheet_name}")
            
            # 从sheet名称中解析剧情ID
            try:
                plot_id = int(sheet_name)
                print(f"    解析剧情ID: {plot_id}")
            except ValueError:
                print(f"    警告: Sheet名称'{sheet_name}'不是有效的数字ID，跳过")
                return
            
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # 查找表头行
            header_row = None
            for idx in range(min(10, len(df))):
                row = df.iloc[idx]
                row_values = [str(v) for v in row.values if pd.notna(v)]
                row_str = ' '.join(row_values)
                
                if '角色' in row_str and '文本内容' in row_str:
                    header_row = idx
                    break
            
            if header_row is None:
                print(f"    警告: 未找到表头行，跳过")
                return
            
            # 重新读取，使用找到的表头行
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
            
            # 跳过第一行（表头描述行）
            if len(df) > 0:
                df = df.iloc[1:]
            
            if len(df) == 0:
                print(f"    警告: 没有数据行，跳过")
                return
            
            print(f"    数据行数: {len(df)}")
            
            # 先记录这个sheet对应的剧情ID
            file_key = (os.path.basename(filename), sheet_name)
            self.file_sheet_to_plot_id[file_key] = plot_id
            
            # 处理这个sheet的所有事件
            # 每个sheet维护自己的上一个事件内容，用于增量存储
            last_event_content = {}
            event_ids = []
            processed_count = 0
            
            # 先预扫描所有行，确定哪些行有 options
            rows_list = list(df.iterrows())
            rows_with_options = set()
            for i, (idx, row) in enumerate(rows_list):
                options_str = self.get_column_value(row, self.col_indices['options'])
                branches_str = self.get_column_value(row, self.col_indices['branches'])
                if options_str or branches_str:
                    rows_with_options.add(i)
            
            # 处理每一行，判断当前行或下一行是否有 options
            for i, (idx, row) in enumerate(rows_list):
                # 当前行有 options，或者下一行有 options，都需要保留完整内容
                next_has_options = (i + 1) in rows_with_options
                current_has_options = i in rows_with_options
                keep_full_content = current_has_options or next_has_options
                
                event_id = self.process_row(row, sheet_name, filename, last_event_content, keep_full_content)
                if event_id:
                    event_ids.append(event_id)
                    processed_count += 1
            
            if processed_count > 0:
                print(f"    成功处理 {processed_count} 个事件")
            
            # 添加到剧情表
            if event_ids:
                plot_name = f"{os.path.basename(filename).replace('.xlsx', '')}-{sheet_name}"
                self.plot_data.append({
                    '剧情ID': plot_id,  # 使用从sheet名称解析的ID
                    '事件组': '{' + ','.join(map(str, event_ids)) + '}',
                    '前置条件': '',
                    '剧情名字': plot_name
                })
                print(f"    生成剧情ID {plot_id}: {plot_name}, 事件数: {len(event_ids)}")
                
        except Exception as e:
            print(f"  处理工作表 {sheet_name} 时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def get_column_value(self, row, col_idx):
        """
        获取指定列索引的值
        
        参数:
            row: 数据行
            col_idx: 列索引
            
        返回:
            列的值，如果没找到则返回空字符串
        """
        try:
            if col_idx < len(row):
                val = row.iloc[col_idx]
                if pd.notna(val):
                    return str(val).strip()
        except:
            pass
        return ''
    
    def calculate_incremental_content(self, current_content, last_content, keep_full_content=False):
        """
        计算增量事件内容：只返回相对于上一个事件变化的字段
        注意：当 keep_full_content 为 True 时，该行所有字段都保留完整数据
        
        参数:
            current_content: 当前事件的完整内容
            last_content: 上一个事件的完整内容
            keep_full_content: 是否保留完整内容（当前行或下一行有 options 时为 True）
            
        返回:
            增量内容字典
        """
        incremental = {}
        
        # 如果是第一个事件（last_content为空），返回所有内容
        if not last_content:
            return current_content.copy()
        
        # 如果需要保留完整内容，返回完整的当前内容（不做增量处理）
        if keep_full_content:
            return current_content.copy()
        
        # 所有可能的字段
        all_fields = set(current_content.keys()) | set(last_content.keys())
        
        for field in all_fields:
            current_value = current_content.get(field, '')
            last_value = last_content.get(field, '')
            
            # 如果值发生变化
            if current_value != last_value:
                if current_value:
                    # 有新值，记录新值
                    incremental[field] = current_value
                else:
                    # 从有值变为空，记录为null
                    incremental[field] = 'null'
        
        return incremental
    
    def process_row(self, row, sheet_name, filename, last_event_content, keep_full_content=False):
        """
        处理单行数据，生成事件和对话
        
        参数:
            row: 数据行
            sheet_name: 工作表名称
            filename: 文件名
            last_event_content: 上一个事件的内容字典（用于增量存储）
            keep_full_content: 是否保留完整内容（当前行或下一行有 options 时为 True）
            
        返回:
            event_id: 生成的事件ID，如果没有生成则返回None
        """
        try:
            # 获取角色和文本内容
            role = self.get_column_value(row, self.col_indices['role'])
            text = self.get_column_value(row, self.col_indices['text'])
            
            # 构建当前事件的完整内容
            current_full_content = {}
            
            # 添加角色信息
            if role:
                current_full_content['role'] = role
            
            # 检查所有其他字段
            field_mapping = {
                'event': 'event',
                'music': 'music',
                'audio': 'audio',
                'voice': 'voice',
                'animation': 'animation',
                'action': 'action',
                'painting': 'painting',
                'bgAnim': 'bgAnim',
                'bg': 'bg',
                'props': 'props',
                'jump': 'jump',
                'dialog': 'dialog',
                'nobacktracking': 'nobacktracking',
                'ending': 'ending',
                'jumpStory': 'jumpStory',
                'specialOption': 'specialOption'
            }
            
            for field_key, output_key in field_mapping.items():
                if field_key in self.col_indices:
                    value = self.get_column_value(row, self.col_indices[field_key])
                    if value:
                        current_full_content[output_key] = value
            
            # 先检查是否有选项数据（在判断是否跳过之前）
            options_str = self.get_column_value(row, self.col_indices['options'])
            branches_str = self.get_column_value(row, self.col_indices['branches'])
            has_options = bool(options_str or branches_str)
            
            # 检查是否有任何有效内容（角色、文本或其他事件字段或选项）
            has_text = bool(text)
            has_content = bool(current_full_content)
            
            # 如果所有字段都为空，则跳过这一行
            if not has_text and not has_content and not has_options:
                return None
            
            # 处理跳转选项和跳转分支（options_str 和 branches_str 已在前面获取）
            # 调试输出
            if options_str or branches_str:
                print(f"      检测到选项数据: options='{options_str}', branches='{branches_str}'")
            
            if options_str and branches_str:
                # 创建选项表项
                option_id = self.create_option(options_str, branches_str, filename)
                if option_id:
                    current_full_content['options'] = str(option_id)
                    print(f"      创建选项ID: {option_id}")
            elif options_str or branches_str:
                print(f"      警告: 选项和分支不完整，跳过")
                print(f"      options列索引: {self.col_indices['options']}, 值: '{options_str}'")
                print(f"      branches列索引: {self.col_indices['branches']}, 值: '{branches_str}'")
            
            # 生成对话内容（即使文本为空，也要生成对话ID）
            content_id = self.content_id
            self.content_data.append({
                '对话ID': content_id,
                '中文': text,
                '英文': ''
            })
            self.content_id += 1
            
            # 计算增量：只保存相对于上一个事件变化的字段
            incremental_content = self.calculate_incremental_content(
                current_full_content, 
                last_event_content,
                keep_full_content
            )
            
            # 更新 last_event_content 为当前的完整内容
            last_event_content.clear()
            last_event_content.update(current_full_content)
            
            # 生成事件
            event_id = self.event_id
            event_name = f"{os.path.basename(filename).replace('.xlsx', '')}"
            
            # 将增量事件内容转换为字符串格式
            event_content_str = self.format_event_content(incremental_content)
            
            self.event_data.append({
                '事件ID': event_id,
                '对话内容ID': content_id,
                '事件名': event_name,
                '事件内容': event_content_str
            })
            self.event_id += 1
            
            return event_id
            
        except Exception as e:
            print(f"    处理行时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_option(self, options_str, branches_str, filename):
        """
        创建选项表项
        
        参数:
            options_str: 选项字符串，如"跑,什么都不做,伸手挡住"
            branches_str: 分支字符串，如"Sheet2,Sheet3,Sheet4"
            filename: 当前文件名
            
        返回:
            option_id: 创建的选项ID，如果失败则返回None
        """
        try:
            # 解析选项和分支
            options = [opt.strip() for opt in options_str.split(',')]
            branches = [br.strip() for br in branches_str.split(',')]
            
            print(f"      解析选项: {options}")
            print(f"      解析分支: {branches}")
            
            if len(options) != len(branches):
                print(f"      警告: 选项数量({len(options)})和分支数量({len(branches)})不匹配")
                return None
            
            # 构建选项内容
            option_items = []
            for opt, branch in zip(options, branches):
                # 查找分支对应的剧情ID
                file_key = (os.path.basename(filename), branch)
                if file_key in self.file_sheet_to_plot_id:
                    plot_id = self.file_sheet_to_plot_id[file_key]
                    option_items.append(f'{opt}={plot_id}')
                    print(f"      分支 '{branch}' 映射到剧情ID: {plot_id}")
                else:
                    # 如果还没处理到那个sheet，先用sheet名称占位
                    option_items.append(f'{opt}={branch}')
                    print(f"      分支 '{branch}' 暂时使用占位符（稍后解析）")
            
            option_content = '{' + ','.join(option_items) + '}'
            
            # 添加到选项表
            option_id = self.option_id
            self.option_data.append({
                '选项ID': option_id,
                '选项内容': option_content
            })
            
            # 保存映射关系，用于后续解析
            self.option_to_file[option_id] = (os.path.basename(filename), options_str, branches_str)
            
            self.option_id += 1
            
            print(f"      成功创建选项 {option_id}: {option_content}")
            
            return option_id
            
        except Exception as e:
            print(f"      创建选项时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def format_event_content(self, event_content):
        """
        格式化事件内容为字符串
        
        参数:
            event_content: 事件内容字典
            
        返回:
            格式化后的字符串
        """
        if not event_content:
            return ''
        
        # 格式化为 {key=value,key=value} 的形式
        items = []
        for key, value in event_content.items():
            # 如果值中包含逗号，需要特殊处理
            value_str = str(value).replace('{', '').replace('}', '')
            items.append(f'{key}={value_str}')
        
        return '{' + ','.join(items) + '}'
    
    def resolve_option_branches(self):
        """
        解析选项中未解析的分支引用
        """
        print("\n解析选项中的分支引用...")
        print(f"  当前有 {len(self.option_data)} 个选项待检查")
        print(f"  当前文件-sheet映射表有 {len(self.file_sheet_to_plot_id)} 条记录")
        
        resolved_count = 0
        
        for option in self.option_data:
            option_id = option['选项ID']
            content = option['选项内容']
            
            print(f"  检查选项 {option_id}: {content}")
            
            # 检查是否有未解析的分支（包含Sheet而不是数字）
            if 'Sheet' in content and option_id in self.option_to_file:
                # 获取选项对应的文件名和分支信息
                filename, options_str, branches_str = self.option_to_file[option_id]
                
                print(f"    需要解析: {filename} 的分支 {branches_str}")
                
                # 重新解析
                options = [opt.strip() for opt in options_str.split(',')]
                branches = [br.strip() for br in branches_str.split(',')]
                
                option_items = []
                for opt, branch in zip(options, branches):
                    # 查找分支对应的剧情ID
                    file_key = (filename, branch)
                    if file_key in self.file_sheet_to_plot_id:
                        plot_id = self.file_sheet_to_plot_id[file_key]
                        option_items.append(f'{opt}={plot_id}')
                        resolved_count += 1
                        print(f"      成功: {branch} → 剧情ID {plot_id}")
                    else:
                        # 还是没找到，保持Sheet名称
                        option_items.append(f'{opt}={branch}')
                        print(f"      警告: 未找到分支 '{branch}' 在文件 '{filename}'")
                        print(f"      可用的映射: {[k for k in self.file_sheet_to_plot_id.keys() if k[0] == filename]}")
                
                option['选项内容'] = '{' + ','.join(option_items) + '}'
                print(f"    更新后内容: {option['选项内容']}")
        
        print(f"  成功解析 {resolved_count} 个分支引用")
    
    def save_to_excel(self, output_file):
        """
        保存为Excel文件
        
        参数:
            output_file: 输出文件路径
        """
        try:
            print(f"\n开始生成Excel文件: {output_file}")
            
            # 创建Excel writer
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 剧情表
                plot_df = pd.DataFrame(self.plot_data)
                # 添加表头说明行
                plot_header = pd.DataFrame([{
                    '剧情ID': 'C_INT_PlotID',
                    '事件组': 'C_ARRAY_Events',
                    '前置条件': 'C_TABLE_Conditions',
                    '剧情名字': 'C_STR_PlotKey'
                }])
                plot_df = pd.concat([plot_header, plot_df], ignore_index=True)
                plot_df.to_excel(writer, sheet_name='剧情表', index=False)
                print(f"  剧情表: {len(self.plot_data)} 条记录")
                
                # 事件表
                event_df = pd.DataFrame(self.event_data)
                event_header = pd.DataFrame([{
                    '事件ID': 'C_INT_EventID',
                    '对话内容ID': 'C_STR_ContentID',
                    '事件名': 'C_STR_EventKey',
                    '事件内容': 'C_TABLE_EventContens'
                }])
                event_df = pd.concat([event_header, event_df], ignore_index=True)
                event_df.to_excel(writer, sheet_name='事件表', index=False)
                print(f"  事件表: {len(self.event_data)} 条记录")
                
                # 对话表
                content_df = pd.DataFrame(self.content_data)
                content_header = pd.DataFrame([{
                    '对话ID': 'C_INT_ContentId',
                    '中文': 'C_STR_ZH',
                    '英文': 'C_STR_EN'
                }])
                content_df = pd.concat([content_header, content_df], ignore_index=True)
                content_df.to_excel(writer, sheet_name='对话表', index=False)
                print(f"  对话表: {len(self.content_data)} 条记录")
                
                # 选项表
                if self.option_data:
                    option_df = pd.DataFrame(self.option_data)
                    option_header = pd.DataFrame([{
                        '选项ID': 'C_INT_OptionID',
                        '选项内容': 'C_TABLE_OptionContent'
                    }])
                    option_df = pd.concat([option_header, option_df], ignore_index=True)
                    option_df.to_excel(writer, sheet_name='选项表', index=False)
                    print(f"  选项表: {len(self.option_data)} 条记录")
                else:
                    # 创建空的选项表
                    option_df = pd.DataFrame([{
                        '选项ID': 'C_INT_OptionID',
                        '选项内容': 'C_TABLE_OptionContent'
                    }])
                    option_df.to_excel(writer, sheet_name='选项表', index=False)
                    print(f"  选项表: 0 条记录")
            
            print(f"\n[成功] 成功生成文件: {output_file}")
            
        except Exception as e:
            print(f"保存Excel文件时出错: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    # 获取当前目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 获取所有xlsx文件（不再限制只处理序章）
    xlsx_files = glob.glob("*.xlsx")
    
    # 排除输出文件本身
    xlsx_files = [f for f in xlsx_files if not f.startswith("统一格式-")]
    
    # 按文件名排序
    def sort_key(filename):
        # 优先处理引言
        if '引言' in filename:
            return (-1, 0, filename)
        # 然后处理序章
        match = re.search(r'序章-?(\d+)', filename)
        if match:
            return (0, int(match.group(1)), filename)
        # 其他文件按文件名排序
        else:
            return (1, 0, filename)
    
    xlsx_files.sort(key=sort_key)
    
    print(f"找到 {len(xlsx_files)} 个xlsx文件:")
    for f in xlsx_files:
        print(f"  - {f}")
    
    # 创建转换器
    converter = XlsxConverter()
    
    # 处理所有文件
    for xlsx_file in xlsx_files:
        converter.process_file(xlsx_file)
    
    # 解析选项中的分支引用
    converter.resolve_option_branches()
    
    # 保存结果
    output_filename = "统一格式-所有剧情.xlsx"
    converter.save_to_excel(output_filename)
    
    print("\n" + "="*60)
    print("转换完成！")
    print(f"总计:")
    print(f"  - 剧情数: {len(converter.plot_data)}")
    print(f"  - 事件数: {len(converter.event_data)}")
    print(f"  - 对话数: {len(converter.content_data)}")
    print(f"  - 选项数: {len(converter.option_data)}")
    print(f"\n输出文件: {output_filename}")
    print("="*60)


if __name__ == "__main__":
    main()

