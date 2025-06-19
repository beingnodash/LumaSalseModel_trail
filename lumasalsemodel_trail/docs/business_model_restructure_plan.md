# Luma商业模式重构方案

## 📋 业务需求分析

### 核心业务变化
1. **三种基本商业模式**：
   - **模式A**: 高校付费 + 学生免费使用全部功能
   - **模式B**: 高校付费 + 学生免费基础功能 + 学生付费高级功能
   - **模式C**: 高校免费 + 学生免费基础功能 + 学生付费高级功能

2. **高校客户付费模式**：
   - 3年服务周期，一次性付费
   - 价格可谈判调整
   - 超过3年才考虑续费

3. **学生付费模式**：
   - **按次付费**: 单次使用付费，有复购率
   - **订阅付费**: 月度基础，提供12/36/60个月套餐
   - 基础功能永久免费

4. **分成机制**：
   - 模式A: 无学生付费，无分成
   - 模式B/C: 学生付费与高校分成

## 🏗️ 新参数结构设计

### 1. 基础业务参数
```python
business_model_params = {
    # --- 模拟周期与客户增长 ---
    'total_half_years': 6,  # 总分析周期（建议≥6以观察3年服务周期）
    'new_clients_per_half_year': 5,  # 每半年新签约高校数
    
    # --- 商业模式分布 ---
    'business_mode_distribution': {
        'mode_a': 0.3,  # 高校付费+学生全免费
        'mode_b': 0.4,  # 高校付费+学生分层付费  
        'mode_c': 0.3   # 高校免费+学生分层付费
    },
    
    # --- 高校基础数据 ---
    'avg_students_per_uni': 10000,  # 平均每所高校学生数
    'student_service_period_years': 3,  # 高校服务周期（年）
}
```

### 2. 高校付费参数
```python
university_pricing_params = {
    # --- 高校端定价策略 (3年服务周期) ---
    'uni_pricing_mode_a': {
        'base_price': 600000,  # 模式A基础价格（3年）
        'negotiation_range': (0.7, 1.3),  # 谈判价格范围（70%-130%）
        'price_elasticity': -0.2  # 价格弹性系数
    },
    
    'uni_pricing_mode_b': {
        'base_price': 400000,  # 模式B基础价格（3年）
        'negotiation_range': (0.8, 1.2),
        'price_elasticity': -0.15
    },
    
    'uni_pricing_mode_c': {
        'base_price': 0,  # 模式C免费
        'negotiation_range': (1.0, 1.0),
        'price_elasticity': 0
    },
    
    # --- 高校续约率 (3年后) ---
    'uni_renewal_rates': {
        'mode_a': 0.85,  # 模式A续约率
        'mode_b': 0.80,  # 模式B续约率  
        'mode_c': 0.75   # 模式C续约率
    }
}
```

### 3. 学生付费参数
```python
student_pricing_params = {
    # --- 学生付费转化率 ---
    'student_paid_conversion_rates': {
        'mode_a': 0.0,   # 模式A学生不付费
        'mode_b': 0.08,  # 模式B学生付费转化率
        'mode_c': 0.12   # 模式C学生付费转化率（更高，因为高校免费）
    },
    
    # --- 学生付费方式分布 ---
    'student_payment_method_distribution': {
        'per_use': 0.4,      # 按次付费用户比例
        'subscription': 0.6   # 订阅付费用户比例
    },
    
    # --- 按次付费参数 ---
    'per_use_pricing': {
        'price_per_use': 8.0,  # 单次使用价格
        'avg_uses_per_half_year': 3,  # 平均半年使用次数
        'repurchase_rate': 0.7  # 复购率（学生续费率）
    },
    
    # --- 订阅付费参数 ---
    'subscription_pricing': {
        'monthly_price': 15.0,  # 月度订阅价格
        
        # 套餐定价
        'package_pricing': {
            '12_months': {'price': 150, 'discount_rate': 0.17},  # 年套餐
            '36_months': {'price': 400, 'discount_rate': 0.26},  # 3年套餐
            '60_months': {'price': 600, 'discount_rate': 0.33}   # 5年套餐
        },
        
        # 套餐选择分布
        'package_distribution': {
            'monthly': 0.4,      # 月付用户
            '12_months': 0.45,   # 年付用户
            '36_months': 0.12,   # 3年付用户
            '60_months': 0.03    # 5年付用户
        },
        
        'subscription_renewal_rate': 0.75  # 订阅续费率
    }
}
```

### 4. 分成参数
```python
revenue_sharing_params = {
    # --- 学生付费分成比例 (Luma获得的比例) ---
    'luma_share_from_student_payment': {
        'mode_a': 0.0,   # 无学生付费
        'mode_b': 0.3,   # 模式B: Luma获得30%
        'mode_c': 0.5    # 模式C: Luma获得50%（补偿高校免费）
    }
}
```

## 🔄 收入计算逻辑重构

### 1. 高校端收入计算
```python
def calculate_university_revenue(self, mode, period, cohort_info):
    """计算高校端收入"""
    if mode == 'mode_c':
        return 0  # 模式C高校免费
    
    # 检查是否为首次付费期或续费期
    service_period_half_years = self.params['student_service_period_years'] * 2
    
    if period % service_period_half_years == 0:  # 续费期
        # 计算3年期续费收入
        base_price = self.params[f'uni_pricing_{mode}']['base_price']
        renewal_rate = self.params['uni_renewal_rates'][mode]
        
        # 应用价格谈判和续约率
        actual_revenue = self._apply_price_negotiation(base_price, mode)
        return actual_revenue * renewal_rate
    
    return 0  # 非续费期无高校收入
```

### 2. 学生端收入计算
```python
def calculate_student_revenue(self, mode, active_students, period):
    """计算学生端收入"""
    if mode == 'mode_a':
        return {'total': 0, 'luma_share': 0, 'uni_share': 0}
    
    # 计算付费学生数
    conversion_rate = self.params['student_paid_conversion_rates'][mode]
    paying_students = active_students * conversion_rate
    
    # 按次付费收入
    per_use_revenue = self._calculate_per_use_revenue(paying_students)
    
    # 订阅付费收入
    subscription_revenue = self._calculate_subscription_revenue(paying_students)
    
    total_student_revenue = per_use_revenue + subscription_revenue
    
    # 计算分成
    luma_share_rate = self.params['luma_share_from_student_payment'][mode]
    luma_share = total_student_revenue * luma_share_rate
    uni_share = total_student_revenue * (1 - luma_share_rate)
    
    return {
        'total': total_student_revenue,
        'luma_share': luma_share,
        'uni_share': uni_share
    }
```

### 3. 按次付费收入计算
```python
def _calculate_per_use_revenue(self, paying_students):
    """计算按次付费收入"""
    per_use_ratio = self.params['student_payment_method_distribution']['per_use']
    per_use_students = paying_students * per_use_ratio
    
    price_per_use = self.params['per_use_pricing']['price_per_use']
    avg_uses = self.params['per_use_pricing']['avg_uses_per_half_year']
    
    return per_use_students * price_per_use * avg_uses
```

### 4. 订阅付费收入计算
```python
def _calculate_subscription_revenue(self, paying_students):
    """计算订阅付费收入"""
    sub_ratio = self.params['student_payment_method_distribution']['subscription']
    sub_students = paying_students * sub_ratio
    
    package_dist = self.params['subscription_pricing']['package_distribution']
    package_pricing = self.params['subscription_pricing']['package_pricing']
    monthly_price = self.params['subscription_pricing']['monthly_price']
    
    total_revenue = 0
    
    # 月付用户 (半年收入)
    monthly_users = sub_students * package_dist['monthly']
    total_revenue += monthly_users * monthly_price * 6
    
    # 套餐用户 (一次性付费，分摊到有效期)
    for package, ratio in package_dist.items():
        if package != 'monthly':
            package_users = sub_students * ratio
            package_price = package_pricing[package]['price']
            # 将套餐价格分摊到其有效期的每个半年
            months = int(package.split('_')[0])
            half_year_revenue = (package_price / months) * 6
            total_revenue += package_users * half_year_revenue
    
    return total_revenue
```

## 📊 数据结构调整

### 新的Cohort数据结构
```python
cohort_structure = {
    'cohort_id': 'C_H1',  # 群组标识
    'created_period': 1,   # 创建周期
    'business_mode': 'mode_b',  # 商业模式
    'universities': {
        'total_count': 5,
        'active_count': 4,  # 续约后的活跃数量
        'price_negotiated': 0.9  # 实际谈判价格比例
    },
    'students': {
        'total_per_uni': 10000,
        'paying_per_uni': 800,
        'active_paying_per_uni': 600,  # 考虑续约率
        'payment_methods': {
            'per_use': 240,
            'subscription': 360
        }
    },
    'revenue_history': [
        # 每期收入记录
    ]
}
```

### 输出DataFrame结构调整
```python
output_columns = [
    'period',
    'period_name',
    
    # 高校收入
    'uni_revenue_new_signups',
    'uni_revenue_renewals', 
    'uni_revenue_total',
    
    # 学生收入
    'student_revenue_per_use',
    'student_revenue_subscription',
    'student_revenue_total',
    
    # Luma收入分解
    'luma_revenue_from_uni',
    'luma_revenue_from_student_share',
    'luma_revenue_total',
    
    # 高校收入分解
    'uni_income_from_student_share',
    
    # 业务指标
    'active_universities',
    'total_paying_students',
    'avg_revenue_per_uni',
    'avg_revenue_per_paying_student'
]
```