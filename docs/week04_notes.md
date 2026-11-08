# CourseHub - Buoi 4

- Migration 001: enrollment_events.
- Demo class: RACE-01, capacity = 1.
- POST /enrollments: lock class_sections bang FOR UPDATE.
- Concurrency test: 1 request 201, 1 request 409.
- Performance data: 100000 rows, dataset=performance.
- Index: idx_enrollment_events_dataset_student_time.

## Performance

### Truoc index
- Scan type: Seq Scan.
- Rows Removed by Filter: 99183.
- Buffers: shared hit=1140.

### Sau index
- Scan type: Index Scan.
- Buffers: shared hit=50 read=3.
- Planning Time: 4.635 ms.
- Execution Time: 5.614 ms.
- Rows returned: 50.

Ket qua cho thay composite index giup PostgreSQL tim truc tiep vung du lieu
phu hop thay vi quet phan lon bang enrollment_events.

Khong commit backend/.env.