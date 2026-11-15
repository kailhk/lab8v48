#Варіант 48. Гуртовий склад та виробничі замовлення
#Завдання 1. Гуртовий склад: залишки та черга операцій


class Record:
    def __init__(self, record_id: int, kind: str, a: int, b: int):
        self.id = int(record_id)
        self.kind = kind
        self.a = int(a)#a це p, ціна за умовою завдання
        self.b = int(b)#b це q, залишок за умовою завдання

    def value(self):
        return self.a * self.b#Обліковий показник v = p * q для обох типів

    #перевірка додатного x
    def apply(self, op: str, x: int):
        if x <= 0:
            return 'AMOUNT'#Недодатне x завжди дає помилку AMOUNT
        return 'OK'


class RecordA(Record):
    def __init__(self, record_id: int, a: int, b: int):
        super().__init__(record_id, 'A', a, b)

    #Поліморфне застосування операції для типу A
    def apply(self, op: str, x: int):
        res = super().apply(op, x)
        if res != 'OK':
            return res
        if op == 'TAKE':
            #для A мінімальна кількість 1, тому спеціального правила немає
            if self.b - x < 0:
                return 'STOCK'#Недостатній залишок
            self.b -= x
        elif op == 'PUT':
            if self.b + x > 44:#C = 44 за умовою
                return 'SPACE'#Перевищення місткості
            self.b += x
        else:
            return 'RULE'#невідома операція сюди не потрапляє, це про всяк випадок
        return 'OK'


class RecordB(Record):
    def __init__(self, record_id: int, a: int, b: int):
        super().__init__(record_id, 'B', a, b)

    #Поліморфне застосування операції для типу B
    def apply(self, op: str, x: int):
        res = super().apply(op, x)
        if res != 'OK':
            return res
        if op == 'TAKE':
            if x < 5:#R = 5 мінімальна кількість для TAKE типу B за умовою, перевіряється раніше за залишок
                return 'RULE'#Порушення спеціального правила
            if self.b - x < 0:
                return 'STOCK'#Недостатній залишок
            self.b -= x
        elif op == 'PUT':
            if self.b + x > 44:#C = 44 максимальна місткість запису за умовою
                return 'SPACE'#Перевищення місткості
            self.b += x
        else:
            return 'RULE'
        return 'OK'


class RequestQueue:
    def __init__(self, requests):
        self.queue = list(requests)#власна копія, щоб стан був незалежний

    def pop(self):
        if not self.queue:
            return None
        return self.queue.pop(0)#Вилучення за правилом FIFO

    def snapshot(self):
        return list(self.queue)#окремий список, зміна якого не чіпає чергу


#Головний клас
class System:
    def __init__(self, records, requests):
        self.records = list(records)#власний список у початковому порядку
        self.queue = RequestQueue(requests)
        self.processed = []

    def snapshot(self):
        return [(r.id, r.kind, r.a, r.b, r.value()) for r in self.records]

    def execute_next(self):
        req = self.queue.pop()
        if req is None:
            return None
        j, op, req_id, x = req
        rec = linear_search(self.records, req_id)
        if rec is None:
            status = 'MISSING'#Запис із таким id не знайдено
            state = None
        else:
            status = rec.apply(op, x)#apply викликається рівно один раз
            if status == 'OK':
                state = (rec.b,)#для успіху завдання 1 це нове q
            else:
                state = None
        self.processed.append((j, status, state))
        return (j, status, state)

    #Генерація повного результату
    def result(self, s, g, T):
        lines_out = []
        u = 0
        e = 0
        for j, status, state in self.processed:
            if status == 'OK':
                u += 1
                lines_out.append(f"OP {j} OK {state[0]}")
            else:
                e += 1
                lines_out.append(f"OP {j} {status}")

        lines_out.append(f"PROCESSED {u} {e}")

        w = len(self.queue.snapshot())
        lines_out.append(f"PENDING {w}")

        for j, op, rid, x in self.queue.snapshot():
            lines_out.append(f"WAIT {j} {op} {rid} {x}")

        #Використовуємо обидва пошуки, для бінарного готуємо окрему колекцію за зростанням id
        sorted_by_id = sort_records(self.records, lambda r: r.id)
        found_lin = linear_search(self.records, s)
        found_bin = binary_search(sorted_by_id, s)
        target = found_lin#обидва пошуки дають один і той самий запис

        if target is None:
            lines_out.append("FOUND NONE")
        else:
            lines_out.append(f"FOUND {target.id} {target.kind} {target.a} {target.b} {target.value()}")

        #Відбір: залишок більший за 0, потрібний тип і v не менше T
        selected = []
        for r in self.records:
            if r.b > 0:
                if g == 'ALL' or r.kind == g:
                    if r.value() >= T:
                        selected.append(r)

        #спочатку за id, потім стабільно за спаданням v, тому за однакових v лишається порядок за id
        sorted_by_id = sort_records(selected, lambda r: r.id)
        sorted_final = sort_records(sorted_by_id, lambda r: -r.value())

        h = len(sorted_final)
        lines_out.append(f"SELECT {h}")
        for r in sorted_final:
            lines_out.append(f"ITEM {r.id} {r.kind} {r.a} {r.b} {r.value()}")

        total_q = sum(r.b for r in self.records)
        total_v = sum(r.value() for r in self.records)
        lines_out.append(f"TOTAL {total_q} {total_v}")

        return lines_out


#стабільне сортування злиттям
def sort_records(records, key):
    lst = list(records)
    if len(lst) <= 1:
        return lst

    #Допоміжна функція злиття двох відсортованих частин
    def merge(left, right):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if key(left[i]) <= key(right[j]):#<= щоб сортування було стабільним
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    def merge_sort(arr):
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = merge_sort(arr[:mid])
        right = merge_sort(arr[mid:])
        return merge(left, right)

    return merge_sort(lst)


#Лінійний пошук запису за id у переданому порядку
def linear_search(records, s):
    for r in records:
        if r.id == s:
            return r
    return None


#Бінарний пошук запису за зростанням id (список вже має бути відсортований)
def binary_search(records, s):
    low = 0
    high = len(records) - 1
    while low <= high:
        mid = (low + high) // 2
        if records[mid].id == s:
            return records[mid]
        elif records[mid].id < s:
            low = mid + 1
        else:
            high = mid - 1
    return None


#Перевірка діапазонів запису
def validate_record(id, kind, a, b):
    if not (1 <= id <= 999):#за умовою
        return False
    if kind not in ('A', 'B'):#Допустимі типи A або B
        return False
    if not (1 <= a <= 10000):#ціна p
        return False
    if not (0 <= b <= 44):#залишок q від 0 до C = 44
        return False
    return True


#Перевірка діапазонів запиту
def validate_request(op, id, x):
    if op not in ('TAKE', 'PUT'):#Допустимі операції TAKE або PUT
        return False
    if not (1 <= id <= 999):#за умовою
        return False
    if not (-100 <= x <= 100):#x може бути нульовим і від'ємним, відхиляється воно пізніше
        return False
    return True


#Зчитування вхідних даних з консолі
def read_input():
    N = int(input().strip())

    records = []
    for _ in range(N):
        parts = input().strip().split()
        rid = int(parts[0])
        kind = parts[1]
        p = int(parts[2])
        q = int(parts[3])
        if validate_record(rid, kind, p, q):
            if kind == 'A':
                records.append(RecordA(rid, p, q))
            else:
                records.append(RecordB(rid, p, q))

    M = int(input().strip())

    requests = []
    for j in range(1, M + 1):
        parts = input().strip().split()
        op = parts[0]
        rid = int(parts[1])
        x = int(parts[2])
        if validate_request(op, rid, x):
            requests.append((j, op, rid, x))#j це позиція серед усіх M запитів

    K = int(input().strip())

    s_parts = input().strip().split()
    s = int(s_parts[0])
    g = s_parts[1]
    T = int(s_parts[2])

    return records, requests, K, s, g, T


#Головна функція для запуску програми
def main():
    records, requests, K, s, g, T = read_input()
    system = System(records, requests)
    for _ in range(K):
        system.execute_next()
    res_lines = system.result(s, g, T)
    for line in res_lines:
        print(line)


if __name__ == '__main__':
    main()