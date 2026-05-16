// Выбирает учебную базу MongoDB для документов feedback.
const database = db.getSiblingDB('university');

// Пересоздает коллекцию, чтобы повторный ручной запуск был предсказуемым.
database.submission_feedback.drop();

// Читает CSV из набора model4_university, смонтированного в контейнер MongoDB.
const fs = require('fs');
const csvText = fs.readFileSync('/seed-data/mongodb/submission_feedback.csv', 'utf8');

// Разбирает одну CSV-строку с поддержкой кавычек и экранированных кавычек.
function parseCsvLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const nextChar = line[index + 1];

    if (char === '"' && inQuotes && nextChar === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      values.push(current);
      current = '';
    } else {
      current += char;
    }
  }

  values.push(current);
  return values;
}

// Преобразует CSV в документы MongoDB с rubric и max_points.
const lines = csvText.trim().split(/\r?\n/);
const headers = parseCsvLine(lines[0]);
const documents = [];

for (let rowIndex = 1; rowIndex < lines.length; rowIndex += 1) {
  const values = parseCsvLine(lines[rowIndex]);
  const row = {};

  headers.forEach((header, index) => {
    row[header] = values[index];
  });

  const rubric = JSON.parse(row.rubric).map((item) => ({
    criterion: item.criterion,
    points: item.points,
    max_points: 5,
    comment: item.comment,
  }));

  documents.push({
    _id: row._id,
    submission_id: Number(row.submission_id),
    teacher_id: Number(row.teacher_id),
    ts: row.ts,
    rubric,
    overall_comment: row.overall_comment,
  });
}

// Загружает feedback из архивного CSV.
database.submission_feedback.insertMany(documents);

// Добавляет индекс для быстрых соединений по submission_id.
database.submission_feedback.createIndex({ submission_id: 1 }, { unique: true });
