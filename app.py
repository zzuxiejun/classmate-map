#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同学城市分布地图 - 生产版
基于 Flask + ECharts 的交互式可视化
部署到 Render.com / Railway 等云平台
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'classmate-map-2026')

# 数据存储路径（兼容云平台）
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'classmates.xlsx')
TEMPLATE_DIR = 'templates'

# 确保目录存在
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)


def load_data():
    """加载同学数据"""
    if not os.path.exists(DATA_FILE):
        # 创建示例数据
        sample_data = {
            '姓名': ['张三', '李四', '王五', '赵六', '钱七'],
            '城市': ['北京', '上海', '深圳', '广州', '杭州'],
            '微信': ['wxid_abc', 'wxid_def', 'wxid_ghi', 'wxid_jkl', 'wxid_mno'],
            '职业': ['工程师', '设计师', '教师', '医生', '产品经理'],
            '备注': ['班长', '', '', '学习委员', '']
        }
        df = pd.DataFrame(sample_data)
        df.to_excel(DATA_FILE, index=False)
        return df
    
    try:
        df = pd.read_excel(DATA_FILE)
        return df
    except Exception as e:
        print(f"加载数据失败: {e}")
        return pd.DataFrame()


def get_city_coordinates():
    """从 JSON 文件加载中国城市坐标"""
    try:
        coords_file = os.path.join(os.path.dirname(__file__), 'city_coordinates.json')
        with open(coords_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载城市坐标失败: {e}，使用内置坐标库")
        # 返回最小化的坐标库
        return {
            '北京': [116.4074, 39.9042],
            '上海': [121.4737, 31.2304],
            '广州': [113.2644, 23.1291],
            '深圳': [114.0579, 22.5431]
        }


@app.route('/')
def index():
    """主页 - 地图展示"""
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """API: 获取同学数据"""
    df = load_data()
    
    if df.empty:
        return jsonify({
            'cityStats': {},
            'mapData': [],
            'classmates': [],
            'totalCount': 0,
            'cityCount': 0
        })
    
    # 统计城市分布
    city_stats = df['城市'].value_counts().to_dict()
    
    # 准备地图数据
    cities_coords = get_city_coordinates()
    map_data = []
    
    for city, count in city_stats.items():
        # 尝试精确匹配
        if city in cities_coords:
            map_data.append({
                'name': city,
                'value': [cities_coords[city][0], cities_coords[city][1], count],
                'count': count
            })
        else:
            # 尝试模糊匹配（去掉"市"字）
            city_short = city.replace('市', '')
            for coord_city, coords in cities_coords.items():
                if city_short in coord_city or coord_city.replace('市', '') == city_short:
                    map_data.append({
                        'name': coord_city,
                        'value': [coords[0], coords[1], count],
                        'count': count
                    })
                    break
    
    # 同学列表
    classmates = df.to_dict('records')
    
    return jsonify({
        'cityStats': city_stats,
        'mapData': map_data,
        'classmates': classmates,
        'totalCount': len(df),
        'cityCount': len(city_stats)
    })


@app.route('/api/add', methods=['POST'])
def add_classmate():
    """API: 添加同学"""
    try:
        data = request.json
        
        # 验证必填字段
        if not data.get('姓名') or not data.get('城市'):
            return jsonify({'success': False, 'message': '姓名和城市为必填项'}), 400
        
        df = load_data()
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        
        df.to_excel(DATA_FILE, index=False)
        return jsonify({'success': True, 'message': '添加成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/export')
def export_data():
    """导出Excel"""
    try:
        df = load_data()
        export_path = os.path.join(os.path.dirname(__file__), 'data', f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        df.to_excel(export_path, index=False)
        return send_file(export_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin')
def admin():
    """管理页面"""
    df = load_data()
    return render_template('admin.html', classmates=df.to_dict('records'))


@app.route('/health')
def health():
    """健康检查（云平台需要）"""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    # 本地开发用
    port = int(os.environ.get('PORT', 5001))
    print("="*60)
    print("🎓 同学城市分布地图 - 生产版")
    print("="*60)
    print(f"📂 数据文件: {os.path.abspath(DATA_FILE)}")
    print(f"🌐 访问地址: <ADDRESS_REMOVED>
    print("="*60)
    app.run(debug=False, port=port, host='0.0.0.0')
