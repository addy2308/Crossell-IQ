import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
    stages: [
        { duration: '30s', target: 20 },  // ramp up to 20 users
        { duration: '1m', target: 20 },   // stay at 20 users
        { duration: '30s', target: 0 },   // ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
        http_req_failed: ['rate<0.01'],   // less than 1% error rate
    },
};

export default function () {
    let responses = [
        http.get('http://127.0.0.1:8000/health'),
        http.get('http://127.0.0.1:8000/api/v1/dashboard/summary'),
        http.get('http://127.0.0.1:8000/api/v1/predictions/recent?limit=5'),
        http.get('http://127.0.0.1:8000/api/v1/agent/queue?agent_id=test&limit=5'),
    ];

    for (let res of responses) {
        check(res, { 'status is 200': (r) => r.status === 200 });
    }
    sleep(1);
}
