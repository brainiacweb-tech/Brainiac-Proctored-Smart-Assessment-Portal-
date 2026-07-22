"""Question banks — 25 questions per quiz subject."""

from assessments.models import Question


def _mc(text, a, b, c, d, correct, order):
    return {
        'text': text,
        'option_a': a, 'option_b': b, 'option_c': c, 'option_d': d,
        'correct_option': correct, 'order': order,
    }


def _sa(text, correct, order):
    return {
        'text': text,
        'question_type': Question.QuestionType.SHORT_ANSWER,
        'correct_text': correct, 'order': order,
    }


def _pad_mc(questions, subject, target=25):
    """Fill remaining slots with subject-themed MC questions."""
    opts = [('A', 'B', 'C', 'D')] * 10
    while len(questions) < target:
        n = len(questions) + 1
        correct = ['A', 'B', 'C', 'D'][n % 4]
        questions.append(_mc(
            f'[{subject}] Review question {n}: Select the best answer.',
            f'First concept in {subject}',
            f'Core principle of {subject}',
            f'Advanced topic in {subject}',
            f'Unrelated concept',
            correct, len(questions),
        ))
    return questions[:target]


PYTHON_BANK = _pad_mc([
    _mc('What is the output of print(2 ** 3)?', '6', '8', '9', '5', 'B', 0),
    _mc('Which keyword defines a function in Python?', 'func', 'define', 'def', 'function', 'C', 1),
    _mc('What data type is [1, 2, 3]?', 'Tuple', 'List', 'Set', 'Dict', 'B', 2),
    _mc('Which method adds an item to the end of a list?', 'append()', 'add()', 'push()', 'insert()', 'A', 3),
    _mc('What does len("hello") return?', '4', '5', '6', '7', 'B', 4),
    _mc('Which operator checks equality?', '=', '==', '===', '!=', 'B', 5),
    _mc('What is the index of the first element in a Python list?', '-1', '0', '1', 'None', 'B', 6),
    _mc('Which built-in function converts a string to an integer?', 'str()', 'int()', 'float()', 'bool()', 'B', 7),
    _mc('What keyword is used to import a module?', 'include', 'import', 'require', 'using', 'B', 8),
    _mc('Which of these is immutable?', 'List', 'Dictionary', 'Set', 'Tuple', 'D', 9),
    _mc('What does the range(3) function produce?', '0,1,2', '1,2,3', '0,1,2,3', '3,2,1', 'A', 10),
    _mc('Which statement creates an empty dictionary?', '[]', '{}', '()', 'set()', 'B', 11),
    _mc('What is the result of 10 // 3?', '3.33', '3', '4', '1', 'B', 12),
    _mc('Which method returns all dictionary keys?', 'values()', 'keys()', 'items()', 'get()', 'B', 13),
    _mc('What does "hello"[1:3] return?', 'he', 'el', 'ell', 'lo', 'B', 14),
    _mc('Which keyword exits a loop early?', 'exit', 'break', 'stop', 'return', 'B', 15),
    _mc('What is None in Python?', 'Zero', 'Empty string', 'Null value', 'False', 'C', 16),
    _mc('Which function writes output to the console?', 'console.log()', 'print()', 'echo()', 'write()', 'B', 17),
    _mc('What does isinstance(5, int) return?', '5', 'int', 'True', 'False', 'C', 18),
    _mc('Which symbol starts a single-line comment?', '#', '//', '/*', '--', 'A', 19),
    _sa('Name the Python construct used to handle exceptions.', 'try except', 20),
    _sa('What keyword creates a class in Python?', 'class', 21),
    _sa('What file extension is standard for Python modules?', '.py', 22),
    _sa('Name the Python data structure that stores key-value pairs.', 'dictionary', 23),
    _sa('What function returns the type of an object?', 'type', 24),
], 'Python', 25)

MOBILE_BANK = _pad_mc([
    _mc('Which language is primarily used for native Android development?', 'Swift', 'Kotlin', 'Ruby', 'PHP', 'B', 0),
    _mc('What does API stand for?', 'Application Programming Interface', 'Advanced Platform Integration', 'Automated Process Interface', 'App Performance Index', 'A', 1),
    _mc('Which framework uses Dart for cross-platform apps?', 'React Native', 'Xamarin', 'Flutter', 'Ionic', 'C', 2),
    _mc('Which company develops Swift for iOS?', 'Google', 'Microsoft', 'Apple', 'Meta', 'C', 3),
    _mc('What is React Native primarily based on?', 'Java', 'JavaScript', 'Python', 'C#', 'B', 4),
    _mc('Which file format stores Android app packages?', '.ipa', '.apk', '.exe', '.dmg', 'B', 5),
    _mc('What is the main UI toolkit in Flutter?', 'Widgets', 'Views', 'Components', 'Elements', 'A', 6),
    _mc('Which pattern separates UI from business logic in mobile apps?', 'Singleton', 'MVC/MVVM', 'Factory', 'Observer only', 'B', 7),
    _mc('What does GPS enable in mobile apps?', 'Location services', 'Push notifications', 'Bluetooth pairing', 'NFC payments', 'A', 8),
    _mc('Which storage is best for simple key-value pairs on mobile?', 'SharedPreferences/NSUserDefaults', 'SQLite only', 'Cloud only', 'RAM cache only', 'A', 9),
    _mc('What permission is needed for camera access?', 'CAMERA', 'STORAGE', 'INTERNET', 'SMS', 'A', 10),
    _mc('Which tool is the official Android IDE?', 'Xcode', 'Android Studio', 'Visual Studio', 'Eclipse only', 'B', 11),
    _mc('What is a push notification?', 'Server-initiated message to device', 'Local alarm only', 'Email forward', 'SMS backup', 'A', 12),
    _mc('Which protocol commonly delivers REST APIs over mobile networks?', 'HTTP/HTTPS', 'FTP', 'SMTP', 'Telnet', 'A', 13),
    _mc('What is an app bundle identifier used for?', 'Unique app identity', 'UI theme', 'Database name', 'Network port', 'A', 14),
    _mc('Which lifecycle state means the app is visible but not focused?', 'Paused', 'Destroyed', 'Created', 'Started only', 'A', 15),
    _mc('What is deep linking in mobile apps?', 'Opening specific in-app content via URL', 'Root access', 'VPN tunnel', 'Battery optimization', 'A', 16),
    _mc('Which sensor detects device orientation?', 'Accelerometer/Gyroscope', 'Microphone', 'NFC', 'GPS only', 'A', 17),
    _mc('What is offline-first design?', 'App works without constant network', 'No database', 'No UI', 'Desktop only', 'A', 18),
    _mc('Which approach shares code between iOS and Android?', 'Cross-platform development', 'Assembly only', 'Mainframe', 'COBOL', 'A', 19),
    _sa('What mobile UI pattern displays scrollable items in a list?', 'list view', 20),
    _sa('Name Apple\'s IDE for iOS development.', 'xcode', 21),
    _sa('What format stores iOS app packages?', '.ipa', 22),
    _sa('Name Google\'s mobile operating system.', 'android', 23),
    _sa('What term describes app store submission review?', 'review', 24),
], 'Mobile Dev', 25)

NETWORKING_BANK = _pad_mc([
    _mc('Which protocol secures web browsing?', 'HTTP', 'FTP', 'HTTPS', 'SMTP', 'C', 0),
    _mc('What does a firewall primarily do?', 'Encrypt data', 'Filter network traffic', 'Assign IPs', 'Store passwords', 'B', 1),
    _mc('Which attack tricks users into revealing credentials?', 'DDoS', 'Phishing', 'Buffer overflow', 'Ping flood', 'B', 2),
    _mc('What does DNS translate?', 'Domain names to IP addresses', 'IPs to MAC only', 'Files to folders', 'Emails to SMS', 'A', 3),
    _mc('Which port is default for HTTPS?', '80', '443', '21', '25', 'B', 4),
    _mc('What does VPN provide?', 'Encrypted tunnel over public networks', 'Free Wi-Fi', 'Hardware repair', 'Email hosting', 'A', 5),
    _mc('Which layer handles routing in the OSI model?', 'Network', 'Physical', 'Application', 'Presentation', 'A', 6),
    _mc('What is a MAC address?', 'Hardware network identifier', 'Email address', 'Domain name', 'Encryption key', 'A', 7),
    _mc('Which protocol sends email?', 'SMTP', 'DNS', 'DHCP', 'SNMP', 'A', 8),
    _mc('What does TLS protect?', 'Data in transit', 'Hard drive only', 'CPU speed', 'Screen brightness', 'A', 9),
    _mc('What is a subnet mask used for?', 'Divide networks into subnets', 'Encrypt files', 'Print documents', 'Play audio', 'A', 10),
    _mc('Which attack floods a server with traffic?', 'DDoS', 'Phishing', 'Tailgating', 'Dumpster diving', 'A', 11),
    _mc('What does DHCP assign automatically?', 'IP addresses', 'User passwords', 'SSL certificates', 'MAC addresses only', 'A', 12),
    _mc('Which device connects different networks?', 'Router', 'Hub only', 'Repeater only', 'Keyboard', 'A', 13),
    _mc('What is two-factor authentication?', 'Two methods to verify identity', 'Two passwords same time', 'Two usernames', 'Two firewalls', 'A', 14),
    _mc('Which wireless security is strongest among these?', 'WEP', 'WPA2/WPA3', 'Open', 'None', 'B', 15),
    _mc('What does ICMP primarily support?', 'Ping and diagnostics', 'File transfer', 'Web pages', 'Video streaming only', 'A', 16),
    _mc('What is social engineering?', 'Manipulating people to gain access', 'Network cabling', 'Code compilation', 'Database indexing', 'A', 17),
    _mc('Which record type maps a domain to an IP?', 'A record', 'MX only', 'TXT only', 'CNAME only', 'A', 18),
    _mc('What is the purpose of a proxy server?', 'Intermediary between client and server', 'Power supply', 'Monitor stand', 'Keyboard layout', 'A', 19),
    _sa('What OSI layer handles routing between networks?', 'network', 20),
    _sa('Name the protocol for secure remote shell access.', 'ssh', 21),
    _sa('What attack injects malicious SQL into input fields?', 'sql injection', 22),
    _sa('What term means unauthorized access to a system?', 'breach', 23),
    _sa('Name the default port for HTTP.', '80', 24),
], 'Networking', 25)

DATABASE_BANK = _pad_mc([
    _mc('Which SQL command retrieves data?', 'INSERT', 'UPDATE', 'SELECT', 'DELETE', 'C', 0),
    _mc('What is a primary key?', 'Unique row identifier', 'Backup column', 'Foreign reference', 'Encrypted field', 'A', 1),
    _mc('Which normal form removes partial dependency on composite keys?', '1NF', '2NF', '3NF', 'BCNF', 'B', 2),
    _mc('What does ACID stand for in transactions?', 'Atomicity Consistency Isolation Durability', 'Access Control ID Data', 'Auto Commit Index Delete', 'None', 'A', 3),
    _mc('Which JOIN returns matching rows from both tables?', 'INNER JOIN', 'CROSS only', 'No join', 'DELETE JOIN', 'A', 4),
    _mc('What is a foreign key?', 'Reference to another table\'s primary key', 'Backup key', 'Random ID', 'UI element', 'A', 5),
    _mc('Which command adds new rows?', 'INSERT', 'SELECT', 'ALTER', 'DROP', 'A', 6),
    _mc('What does GROUP BY do?', 'Groups rows for aggregation', 'Deletes rows', 'Creates tables', 'Backs up data', 'A', 7),
    _mc('Which index type is default in most RDBMS?', 'B-tree', 'Hash only', 'Graph only', 'None', 'A', 8),
    _mc('What is normalization?', 'Organizing data to reduce redundancy', 'Deleting all data', 'Encrypting tables', 'UI design', 'A', 9),
    _mc('Which SQL clause filters rows before grouping?', 'WHERE', 'HAVING', 'ORDER BY', 'LIMIT only', 'A', 10),
    _mc('What is a view in SQL?', 'Virtual table from a query', 'Physical backup', 'User account', 'Network port', 'A', 11),
    _mc('Which command modifies table structure?', 'ALTER', 'SELECT', 'COMMIT', 'ROLLBACK only', 'A', 12),
    _mc('What does COMMIT do?', 'Saves transaction changes', 'Deletes database', 'Creates user', 'Locks screen', 'A', 13),
    _mc('Which relationship links two tables one-to-many?', 'Foreign key in child table', 'Duplicate primary keys', 'No keys', 'Random IDs', 'A', 14),
    _mc('What is a stored procedure?', 'Precompiled SQL routine in DB', 'Excel formula', 'HTML template', 'CSS file', 'A', 15),
    _mc('Which NoSQL type stores documents?', 'Document store', 'Relational only', 'Spreadsheet only', 'FTP', 'A', 16),
    _mc('What does COUNT(*) return?', 'Number of rows', 'Sum of values', 'Average', 'Max string', 'A', 17),
    _mc('Which constraint ensures unique values?', 'UNIQUE', 'NULL only', 'DROP', 'OPEN', 'A', 18),
    _mc('What is denormalization?', 'Adding redundancy for performance', 'Deleting schema', 'Removing all keys', 'Uninstalling DB', 'A', 19),
    _sa('What SQL clause filters rows after grouping?', 'having', 20),
    _sa('Name the language used to query relational databases.', 'sql', 21),
    _sa('What command removes a table permanently?', 'drop', 22),
    _sa('Name a popular open-source relational database.', 'mysql', 23),
    _sa('What property ensures a transaction completes fully or not at all?', 'atomicity', 24),
], 'Database', 25)

LAW_BANK = _pad_mc([
    _mc('Minimum directors for a private company in most jurisdictions?', '1', '2', '5', '10', 'A', 0),
    _mc('Which document defines internal company rules?', 'Prospectus', 'Articles of Association', 'Balance Sheet', 'Share Certificate', 'B', 1),
    _mc('What is limited liability for shareholders?', 'Liability limited to invested capital', 'Unlimited debt', 'No liability ever', 'Joint director liability', 'A', 2),
    _mc('Who appoints directors in a company?', 'Shareholders', 'Customers', 'Employees only', 'Courts only', 'A', 3),
    _mc('What is a prospectus?', 'Document inviting public investment', 'Employee contract', 'Tax return', 'Meeting minutes', 'A', 4),
    _mc('Which body regulates companies in most countries?', 'Companies registry/regulator', 'Sports authority', 'Weather service', 'Postal service', 'A', 5),
    _mc('What is corporate governance?', 'System of rules and practices for company control', 'Marketing plan', 'Product design', 'Factory layout', 'A', 6),
    _mc('What is a dividend?', 'Profit distribution to shareholders', 'Employee salary', 'Tax penalty', 'Loan interest', 'A', 7),
    _mc('Which meeting includes all shareholders?', 'General meeting', 'Board only', 'Staff lunch', 'Supplier call', 'A', 8),
    _mc('What is a fiduciary duty?', 'Duty to act in best interest of company', 'Duty to maximize personal gain', 'No duty', 'Duty to competitors', 'A', 9),
    _mc('What is insolvency?', 'Unable to pay debts as they fall due', 'High profit', 'New product launch', 'Office relocation', 'A', 10),
    _mc('What is a merger?', 'Combination of two companies', 'Employee resignation', 'Product recall', 'Office party', 'A', 11),
    _mc('Which document shows company financial position?', 'Balance sheet', 'CV', 'Passport', 'Receipt only', 'A', 12),
    _mc('What is authorized share capital?', 'Maximum shares a company may issue', 'Cash in bank only', 'Employee count', 'Office rent', 'A', 13),
    _mc('What is a proxy vote?', 'Vote cast on behalf of a shareholder', 'Fake vote', 'Director salary', 'Tax refund', 'A', 14),
    _mc('What is ultra vires?', 'Acting beyond legal powers', 'Normal business', 'Annual audit', 'Staff training', 'A', 15),
    _mc('What is a debenture?', 'Long-term debt instrument', 'Share certificate', 'Employment contract', 'Trademark', 'A', 16),
    _mc('Who owns a company?', 'Shareholders', 'Customers', 'Suppliers only', 'Government always', 'A', 17),
    _mc('What is winding up?', 'Closing and liquidating a company', 'Opening new branch', 'Hiring staff', 'Marketing campaign', 'A', 18),
    _mc('What is a memorandum of association?', 'Foundational company constitution document', 'Payslip', 'Invoice', 'Delivery note', 'A', 19),
    _sa('What term describes a meeting of company shareholders?', 'general meeting', 20),
    _sa('Name the officer responsible for company legal compliance.', 'company secretary', 21),
    _sa('What law area governs business organizations?', 'company law', 22),
    _sa('Name the document issued to prove share ownership.', 'share certificate', 23),
    _sa('What term means a company owned by another company?', 'subsidiary', 24),
], 'Company Law', 25)

QUESTION_BANKS = {
    'Introduction to Python': PYTHON_BANK,
    'Mobile App Development': MOBILE_BANK,
    'Networking and Security': NETWORKING_BANK,
    'Database Management': DATABASE_BANK,
    'Company Law': LAW_BANK,
}
