# 性能审查指南

> 基于 Core Web Vitals 和业界最佳实践的性能代码审查清单。

---

## 性能严重度等级

| 等级 | 说明 | 动作 |
|------|------|------|
| **🔴 Critical** | 严重影响用户体验，LCP > 4s 或主线程阻塞 > 1s | 阻断合并 |
| **🟠 High** | 明显性能问题，LCP 2.5-4s，未虚拟化长列表 | 建议发布前修复 |
| **🟡 Medium** | 中度风险，未代码分割，未使用索引 | 应修复 |
| **🟢 Low** | 轻微优化机会，图片未优化格式 | 建议修复 |
| **ℹ️ Info** | 优化建议 | 可选 |

---

## 1. 前端性能（Core Web Vitals）

### 2024 核心指标

| 指标 | 全称 | 目标值 | 含义 |
|------|------|--------|------|
| **LCP** | Largest Contentful Paint | ≤ 2.5s | 最大内容绘制时间 |
| **INP** | Interaction to Next Paint | ≤ 200ms | 交互响应时间（2024 年替代 FID）|
| **CLS** | Cumulative Layout Shift | ≤ 0.1 | 累积布局偏移 |
| **FCP** | First Contentful Paint | ≤ 1.8s | 首次内容绘制 |

### LCP 优化检查

```javascript
// ❌ LCP 图片懒加载 - 延迟关键内容
<img src="hero.jpg" loading="lazy" />

// ✅ LCP 图片立即加载
<img src="hero.jpg" fetchpriority="high" />

// ❌ 未优化的图片格式
<img src="hero.png" />  // PNG 文件过大

// ✅ 现代图片格式 + 响应式
<picture>
  <source srcset="hero.avif" type="image/avif" />
  <source srcset="hero.webp" type="image/webp" />
  <img src="hero.jpg" alt="Hero" />
</picture>
```

**审查要点：**
- [ ] LCP 元素是否设置 `fetchpriority="high"`？
- [ ] 是否使用 WebP/AVIF 格式？
- [ ] 是否有服务端渲染或静态生成？
- [ ] CDN 是否配置正确？

### INP 优化检查

```javascript
// ❌ 长任务阻塞主线程
button.addEventListener('click', () => {
  processLargeData(data);  // 耗时 500ms
  updateUI();
});

// ✅ 拆分长任务
button.addEventListener('click', async () => {
  await scheduler.yield?.() ?? new Promise(r => setTimeout(r, 0));
  for (const chunk of chunks) {
    processChunk(chunk);
    await scheduler.yield?.();
  }
  updateUI();
});

// ✅ 使用 Web Worker 处理复杂计算
const worker = new Worker('heavy-computation.js');
worker.postMessage(data);
worker.onmessage = (e) => updateUI(e.data);
```

### CLS 优化检查

```css
/* ❌ 未指定尺寸的媒体 */
img { width: 100%; }

/* ✅ 预留空间 */
img {
  width: 100%;
  aspect-ratio: 16 / 9;
}
```

**CLS 审查清单：**
- [ ] 图片/视频是否有 width/height 或 aspect-ratio？
- [ ] 字体加载是否使用 `font-display: swap`？
- [ ] 动态内容是否预留空间？
- [ ] 是否避免在现有内容上方插入内容？

---

## 2. JavaScript 性能

### 代码分割与懒加载

```javascript
// ❌ 一次性加载所有代码
import { HeavyChart } from './charts';
import { PDFExporter } from './pdf';

// ✅ 按需加载
const HeavyChart = lazy(() => import('./charts'));
```

### Bundle 体积优化

```javascript
// ❌ 导入整个库
import _ from 'lodash';

// ✅ 按需导入
import debounce from 'lodash/debounce';
```

**Bundle 审查清单：**
- [ ] 是否使用动态 import() 进行代码分割？
- [ ] 大型库是否按需导入？
- [ ] 是否分析过 bundle 大小？
- [ ] 是否有未使用的依赖？

---

## 3. 数据库性能

### N+1 查询问题

```python
# ❌ N+1 问题 - 1 + N 次查询
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # N 次查询

# ✅ Eager Loading - 2 次查询
users = User.objects.select_related('profile').all()
```

### 索引优化

```sql
-- ❌ 全表扫描
SELECT * FROM orders WHERE status = 'pending';

-- ✅ 添加索引
CREATE INDEX idx_orders_status ON orders(status);
```

### 查询优化

```sql
-- ❌ SELECT * 获取不需要的列
SELECT * FROM users WHERE id = 1;

-- ✅ 只查询需要的列
SELECT id, name, email FROM users WHERE id = 1;
```

---

## 4. 算法复杂度

| 复杂度 | 名称 | 10 条 | 1000 条 | 100 万条 |
|--------|------|-------|----------|------------|
| O(1) | 常数 | 1 | 1 | 1 |
| O(log n) | 对数 | 3 | 10 | 20 |
| O(n) | 线性 | 10 | 1000 | 100 万 |
| O(n²) | 平方 | 100 | 100 万 | 1 万亿 |

```javascript
// ❌ O(n²) - 嵌套循环
function findDuplicates(arr) {
  const duplicates = [];
  for (let i = 0; i < arr.length; i++) {
    for (let j = i + 1; j < arr.length; j++) {
      if (arr[i] === arr[j]) duplicates.push(arr[i]);
    }
  }
  return duplicates;
}

// ✅ O(n) - 使用 Set
function findDuplicates(arr) {
  const seen = new Set();
  const duplicates = new Set();
  for (const item of arr) {
    if (seen.has(item)) duplicates.add(item);
    seen.add(item);
  }
  return [...duplicates];
}
```

---

## 5. 性能审查清单

### 🔴 必须检查（阻塞级）

**前端：**
- [ ] LCP 图片是否懒加载？（不应该）
- [ ] 是否有 `transition: all`？
- [ ] 列表 > 100 项是否虚拟化？

**后端：**
- [ ] 是否存在 N+1 查询？
- [ ] 列表接口是否有分页？
- [ ] 是否有 SELECT * 查大表？

### 🟡 建议检查（重要级）

- [ ] 是否使用代码分割？
- [ ] 热点数据是否有缓存？
- [ ] WHERE 列是否有索引？

---

## 参考资源

- [Core Web Vitals - web.dev](https://web.dev/articles/vitals)
- [MemLab - Meta](https://github.com/facebookincubator/memlab)
- [Big O Cheat Sheet](https://www.bigocheatsheet.com/)
