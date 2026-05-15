// Выбирает учебную базу MongoDB для документов feedback.
db = db.getSiblingDB('university');

// Пересоздает коллекцию, чтобы повторный ручной запуск был предсказуемым.
db.submission_feedback.drop();

// Загружает feedback с массивом критериев rubric.
db.submission_feedback.insertMany([
  {
    submission_id: 5001,
    reviewer: 'Sergey Abramov',
    comment: 'Strong joins and clear aliases.',
    rubric: [
      { criterion: 'correctness', max_points: 6, points: 5.5 },
      { criterion: 'style', max_points: 2, points: 1.8 },
      { criterion: 'tests', max_points: 2, points: 1.7 }
    ]
  },
  {
    submission_id: 5004,
    reviewer: 'Sergey Abramov',
    comment: 'Empty result and no reproducible query.',
    rubric: [
      { criterion: 'correctness', max_points: 6, points: 0 },
      { criterion: 'style', max_points: 2, points: 0.3 },
      { criterion: 'tests', max_points: 2, points: 0 }
    ]
  },
  {
    submission_id: 5007,
    reviewer: 'Sergey Abramov',
    comment: 'Plan analysis is incomplete.',
    rubric: [
      { criterion: 'correctness', max_points: 6, points: 3 },
      { criterion: 'style', max_points: 2, points: 1 },
      { criterion: 'documentation', max_points: 2, points: 1 }
    ]
  },
  {
    submission_id: 5010,
    reviewer: 'Sergey Abramov',
    comment: 'Transaction anomalies are partly missed.',
    rubric: [
      { criterion: 'correctness', max_points: 6, points: 2 },
      { criterion: 'style', max_points: 2, points: 1.2 },
      { criterion: 'tests', max_points: 2, points: 0.8 }
    ]
  },
  {
    submission_id: 5011,
    reviewer: 'Sergey Abramov',
    comment: 'No working transaction scenario.',
    rubric: [
      { criterion: 'correctness', max_points: 6, points: 0 },
      { criterion: 'style', max_points: 2, points: 0.5 },
      { criterion: 'tests', max_points: 2, points: 0 }
    ]
  },
  {
    submission_id: 5014,
    reviewer: 'Natalia Romanova',
    comment: 'Pipeline loads data reliably.',
    rubric: [
      { criterion: 'correctness', max_points: 8, points: 7.5 },
      { criterion: 'performance', max_points: 3, points: 2.5 },
      { criterion: 'documentation', max_points: 4, points: 4 }
    ]
  },
  {
    submission_id: 5017,
    reviewer: 'Natalia Romanova',
    comment: 'Consumer does not start.',
    rubric: [
      { criterion: 'correctness', max_points: 8, points: 0 },
      { criterion: 'performance', max_points: 3, points: 0 },
      { criterion: 'documentation', max_points: 4, points: 0.5 }
    ]
  },
  {
    submission_id: 5019,
    reviewer: 'Natalia Romanova',
    comment: 'Dimensional model is clear.',
    rubric: [
      { criterion: 'correctness', max_points: 8, points: 7 },
      { criterion: 'style', max_points: 3, points: 2.4 },
      { criterion: 'documentation', max_points: 4, points: 3.6 }
    ]
  },
  {
    submission_id: 5022,
    reviewer: 'Boris Lebedev',
    comment: 'Coverage is acceptable, edge cases are weak.',
    rubric: [
      { criterion: 'correctness', max_points: 5, points: 3 },
      { criterion: 'tests', max_points: 4, points: 2 },
      { criterion: 'style', max_points: 1, points: 1 }
    ]
  },
  {
    submission_id: 5024,
    reviewer: 'Sergey Abramov',
    comment: 'Catalog configuration is complete.',
    rubric: [
      { criterion: 'correctness', max_points: 7, points: 6.5 },
      { criterion: 'documentation', max_points: 3, points: 2.5 },
      { criterion: 'style', max_points: 2, points: 2 }
    ]
  },
  {
    submission_id: 5027,
    reviewer: 'Sergey Abramov',
    comment: 'Federated query misses file metrics.',
    rubric: [
      { criterion: 'correctness', max_points: 7, points: 3.5 },
      { criterion: 'documentation', max_points: 3, points: 2 },
      { criterion: 'performance', max_points: 2, points: 1.5 }
    ]
  },
  {
    submission_id: 5029,
    reviewer: 'Sergey Abramov',
    comment: 'Late and missing several joins.',
    rubric: [
      { criterion: 'correctness', max_points: 7, points: 2.5 },
      { criterion: 'documentation', max_points: 3, points: 1.2 },
      { criterion: 'performance', max_points: 2, points: 1.3 }
    ]
  }
]);

// Добавляет индекс для быстрых соединений по submission_id.
db.submission_feedback.createIndex({ submission_id: 1 }, { unique: true });
