#Варіант 48. Гуртовий склад та виробничі замовлення
#Завдання 2. Виробничі замовлення: допустимість операцій і зміни стану


class Record:
    def __init__(self, record_id: int, kind: str, a: int, b: int):
        self.id = int(record_id)
        self.kind = kind
        self.a = int(a)#a доступні одиниці матеріалу
        self.b = int(b)#b готові придатні вироби

    #Обчислення облікового показника v
    def value(self):
        return self.b * 14#P = 14 за умовою

    #перевірка додатного x
    def apply(self, op: str, x: int):
        if x <= 0:
            return 'AMOUNT'#Недодатне x завжди дає помилку AMOUNT
        return 'OK'


class RecordA(Record):
    def __init__(self, record_id: int, a: int, b: int):
        super().__init__(record_id, 'A', a, b)

    #Для A v = b * P
    def value(self):
        return self.b * 14#P = 14

    #Поліморфне застосування операцій для типу A
    def apply(self, op: str, x: int):
        res = super().apply(op, x)
        if res != 'OK':
            return res

        if op == 'MAKE':
            #для A потреба в матеріалі дорівнює x
            if self.a - x < 0:
                return 'RESOURCE'
            self.a -= x
            self.b += x
        elif op == 'REJECT':
            #зменшує b на x, матеріал не повертається
            if self.b - x < 0:
                return 'RESOURCE'
            self.b -= x
        elif op == 'SUPPLY':
            #збільшує a на x, перевищення C дає SPACE
            if self.a + x > 44:#C = 44 за умовою
                return 'SPACE'
            self.a += x
        else:
            return 'RULE'#невідома операція сюди не потрапляє, це про всяк випадок
        return 'OK'


class RecordB(Record):
    def __init__(self, record_id: int, a: int, b: int):
        super().__init__(record_id, 'B', a, b)

    #Для B v = b * P * 2
    def value(self):
        return self.b * 14 * 2#P = 14

    #Поліморфне застосування операцій для типу B
    def apply(self, op: str, x: int):
        res = super().apply(op, x)
        if res != 'OK':
            return res

        if op == 'MAKE':
            #для B потреба в матеріалі дорівнює x * R
            need = x * 5#R = 5
            if self.a - need < 0:
                return 'RESOURCE'
            self.a -= need
            self.b += x
        elif op == 'REJECT':
            if self.b - x < 0:
                return 'RESOURCE'
            self.b -= x
        elif op == 'SUPPLY':
            if self.a + x > 44:#C = 44
                return 'SPACE'
            self.a += x
        else:
            return 'RULE'
        return 'OK'


class RequestQueue:
    def __init__(self, requests):
        self.queue = list(requests)#власна копія, щоб стан був незалежний

    #Вилучення першого запиту з черги за FIFO
    def pop(self):
        if not self.queue:
            return None
        return self.queue.pop(0)

    #Повернення незалежної копії черги
    def snapshot(self):
        return list(self.queue)


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
            status = 'MISSING'#Об'єкт із таким id не знайдено
            state = None
        else:
            status = rec.apply(op, x)#apply викликається рівно один раз
            if status == 'OK':
                state = (rec.a, rec.b)#для успіху завдання 2 це нові a і b
            else:
                state = None#при відхиленні apply нічого не змінює
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
                lines_out.append(f"OP {j} OK {state[0]} {state[1]}")
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
        target = found_lin#обидва пошуки дають один і той самий об'єкт

        if target is None:
            lines_out.append("FOUND NONE")
        else:
            lines_out.append(f"FOUND {target.id} {target.kind} {target.a} {target.b} {target.value()}")

        #Відбір за типом і v >= T, нульові поля не виключають об'єкт
        selected = []
        for r in self.records:
            if g == 'ALL' or r.kind == g:
                if r.value() >= T:
                    selected.append(r)

        #спочатку за id, потім стабільно за спаданням v
        sorted_by_id = sort_records(selected, lambda r: r.id)
        sorted_final = sort_records(sorted_by_id, lambda r: -r.value())

        h = len(sorted_final)
        lines_out.append(f"SELECT {h}")
        for r in sorted_final:
            lines_out.append(f"ITEM {r.id} {r.kind} {r.a} {r.b} {r.value()}")

        #a тут не стан заявки, тому підсумок це суми a, b та v усіх об'єктів
        total_a = sum(r.a for r in self.records)
        total_b = sum(r.b for r in self.records)
        total_v = sum(r.value() for r in self.records)
        lines_out.append(f"TOTAL {total_a} {total_b} {total_v}")

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

    #сортування злиттям
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
    if not (0 <= a <= 44):#0 <= a <= C, де C = 44
        return False
    if not (0 <= b <= 10000):#0 <= b <= 10000 тільки для початкових даних
        return False
    return True


#Перевірка діапазонів запиту
def validate_request(op, id, x):
    if op not in ('MAKE', 'REJECT', 'SUPPLY'):#Допустимі операції MAKE, REJECT або SUPPLY
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
        a = int(parts[2])
        b = int(parts[3])
        if validate_record(rid, kind, a, b):
            if kind == 'A':
                records.append(RecordA(rid, a, b))
            else:
                records.append(RecordB(rid, a, b))

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