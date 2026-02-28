import re
import json

# Читаем файл
with open('C:\\Users\\Alisherka\\Desktop\\сабак\\PP2\\prac5\\examples\\raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Все цены - убрали ?:
prices = re.findall(r'\d{1,3}( \d{3})*,\d{2}', text)
print("Prices: ", prices[::1])

# Названия товаров
items = re.findall(r'^\d+\.\s*(.+)', text, re.MULTILINE)
print("\n2. Товары:")
for i, item in enumerate(items[::1], 1):
    print(f"   {i}. {item}")

# Общая сумма
total = re.search(r'ИТОГО:\s*([\d\s,]+)', text)
if total:
    total_sum = total.group(1).replace(' ', '').replace(',', '.')
    print(f"\n3. Итого: {float(total_sum):.2f}")

# Дата и время
dt = re.search(r'Время:\s*([\d.]+)\s+([\d:]+)', text)
if dt:
    print(f"\n4. Дата: {dt.group(1)} Время: {dt.group(2)}")

# Способ оплаты
payment = re.search(r'(Банковская карта|Наличные)', text)
if payment:
    print(f"\n5. Оплата: {payment.group(1)}")

# Сохраняем в JSON
data = {
    "total": float(total_sum) if total else 0,
    "date": dt.group(1) if dt else "",
    "items_count": len(items),
    "payment": payment.group(1) if payment else ""
}

with open('receipt.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n6. Данные сохранены в receipt.json")