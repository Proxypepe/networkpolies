import requests
import json
import time
from typing import List, Dict

class SonarQubeRulesMigrator:
    def __init__(self, source_url: str, source_token: str, target_url: str, target_token: str):
        self.source_url = source_url.rstrip('/')
        self.target_url = target_url.rstrip('/')
        self.source_headers = {'Authorization': f'Bearer {source_token}'}
        self.target_headers = {'Authorization': f'Bearer {target_token}'}
        
    def get_rules_from_source(self, repository: str = 'sonarsecrets') -> List[Dict]:
        """Получить правила из исходного SonarQube"""
        rules = []
        page = 1
        page_size = 100
        
        print(f"Получение правил из репозитория {repository}...")
        
        while True:
            params = {
                'repositories': repository,
                'ps': page_size,
                'p': page
            }
            
            response = requests.get(
                f"{self.source_url}/api/rules/search",
                headers=self.source_headers,
                params=params
            )
            
            if response.status_code != 200:
                print(f"Ошибка при получении правил: {response.status_code}")
                break
                
            data = response.json()
            rules.extend(data['rules'])
            
            print(f"Получено страница {page}: {len(data['rules'])} правил")
            
            if len(data['rules']) < page_size:
                break
                
            page += 1
            time.sleep(0.1)  # Чтобы не перегружать API
            
        print(f"Всего получено {len(rules)} правил")
        return rules
    
    def get_rule_details(self, rule_key: str) -> Dict:
        """Получить детальную информацию о правиле"""
        response = requests.get(
            f"{self.source_url}/api/rules/show",
            headers=self.source_headers,
            params={'key': rule_key}
        )
        
        if response.status_code == 200:
            return response.json()['rule']
        else:
            print(f"Ошибка при получении деталей правила {rule_key}: {response.status_code}")
            return None
    
    def rule_exists_in_target(self, rule_key: str) -> bool:
        """Проверить, существует ли правило в целевом инстансе"""
        response = requests.get(
            f"{self.target_url}/api/rules/show",
            headers=self.target_headers,
            params={'key': rule_key}
        )
        return response.status_code == 200
    
    def create_rule_in_target(self, rule_details: Dict) -> bool:
        """Создать правило в целевом инстансе"""
        # Базовые параметры для создания правила
        params = {
            'custom_key': rule_details['key'],
            'name': rule_details['name'],
            'description': rule_details.get('htmlDesc', rule_details.get('mdDesc', '')),
            'severity': rule_details.get('severity', 'MAJOR'),
            'type': rule_details.get('type', 'VULNERABILITY'),
            'status': rule_details.get('status', 'READY')
        }
        
        # Добавляем дополнительные параметры, если они есть
        if 'mdDesc' in rule_details:
            params['markdown_description'] = rule_details['mdDesc']
        
        # Для правил секретов обычно используется определенный шаблон
        response = requests.post(
            f"{self.target_url}/api/rules/create",
            headers=self.target_headers,
            params=params
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ Правило {rule_details['key']} создано успешно")
            return True
        else:
            print(f"✗ Ошибка при создании правила {rule_details['key']}: {response.status_code} - {response.text}")
            return False
    
    def update_rule_in_target(self, rule_key: str, updates: Dict) -> bool:
        """Обновить существующее правило"""
        params = updates.copy()
        params['key'] = rule_key
        
        response = requests.post(
            f"{self.target_url}/api/rules/update",
            headers=self.target_headers,
            params=params
        )
        
        if response.status_code == 200:
            print(f"✓ Правило {rule_key} обновлено успешно")
            return True
        else:
            print(f"✗ Ошибка при обновлении правила {rule_key}: {response.status_code}")
            return False
    
    def migrate_rules(self, repository: str = 'sonarsecrets', dry_run: bool = False):
        """Основной метод миграции правил"""
        print("=== Начало миграции правил ===")
        print(f"Источник: {self.source_url}")
        print(f"Цель: {self.target_url}")
        print(f"Режим dry run: {dry_run}")
        
        # Получаем правила из источника
        rules = self.get_rules_from_source(repository)
        
        if not rules:
            print("Не найдено правил для миграции")
            return
        
        # Статистика
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for rule in rules:
            rule_key = rule['key']
            
            print(f"\nОбработка правила: {rule_key} - {rule['name']}")
            
            # Пропускаем деактивированные правила
            if rule.get('status') != 'READY':
                print(f"✗ Правило {rule_key} пропущено (статус: {rule.get('status')})")
                skip_count += 1
                continue
            
            # Проверяем, существует ли правило в целевом инстансе
            if self.rule_exists_in_target(rule_key):
                print(f"✓ Правило {rule_key} уже существует в целевом инстансе")
                skip_count += 1
                continue
            
            if dry_run:
                print(f"✓ Правило {rule_key} будет создано (dry run)")
                success_count += 1
                continue
            
            # Получаем детальную информацию о правиле
            rule_details = self.get_rule_details(rule_key)
            if not rule_details:
                error_count += 1
                continue
            
            # Создаем правило в целевом инстансе
            if self.create_rule_in_target(rule_details):
                success_count += 1
            else:
                error_count += 1
            
            # Небольшая пауза чтобы не перегружать API
            time.sleep(0.2)
        
        # Выводим статистику
        print(f"\n=== Миграция завершена ===")
        print(f"Успешно: {success_count}")
        print(f"Пропущено: {skip_count}")
        print(f"Ошибки: {error_count}")
        print(f"Всего обработано: {len(rules)}")
    
    def export_rules_to_file(self, filename: str, repository: str = 'sonarsecrets'):
        """Экспорт правил в файл для ручного анализа"""
        rules = self.get_rules_from_source(repository)
        
        export_data = {
            'export_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source_url': self.source_url,
            'rules_count': len(rules),
            'rules': rules
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"Правила экспортированы в файл: {filename}")

def main():
    # Конфигурация
    SOURCE_URL = "http://source-sonarqube:9000"
    SOURCE_TOKEN = "your_source_token"
    
    TARGET_URL = "http://target-sonarqube:9000"
    TARGET_TOKEN = "your_target_token"
    
    # Создаем мигратор
    migrator = SonarQubeRulesMigrator(SOURCE_URL, SOURCE_TOKEN, TARGET_URL, TARGET_TOKEN)
    
    # Сначала экспортируем правила для анализа
    migrator.export_rules_to_file('sonarqube_rules_export.json')
    
    # Запускаем миграцию (сначала в режиме dry run)
    print("Запуск dry run...")
    migrator.migrate_rules(dry_run=True)
    
    # Если все ок, запускаем реальную миграцию
    input("\nНажмите Enter для начала реальной миграции или Ctrl+C для отмены...")
    
    print("Запуск реальной миграции...")
    migrator.migrate_rules(dry_run=False)

if __name__ == "__main__":
    main()
