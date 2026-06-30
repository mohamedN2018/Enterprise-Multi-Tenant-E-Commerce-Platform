import { useCallback, useEffect, useState } from 'react';
import { Alert, Card, Col, Row, Spinner, Table } from 'react-bootstrap';

import { apiGet, errorMessage } from 'api/client';
import { useStore } from 'contexts/StoreContext';

const STAT_CARDS = [
  { key: 'revenue', label: 'Revenue (confirmed)', icon: 'payments', color: 'success' },
  { key: 'count', label: 'Orders', icon: 'receipt_long', color: 'primary' },
  { key: 'confirmed', label: 'Confirmed orders', icon: 'task_alt', color: 'info' },
  { key: 'events', label: 'Tracked events', icon: 'insights', color: 'warning' }
];

export default function Overview() {
  const { activeStore } = useStore();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!activeStore) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      setSummary(await apiGet('/analytics/summary/'));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [activeStore]);

  useEffect(() => {
    load();
  }, [load]);

  const values = {
    revenue: summary ? `${summary.orders?.revenue ?? '0.00'} ${activeStore?.currency || ''}` : '—',
    count: summary?.orders?.count ?? '—',
    confirmed: summary?.orders?.confirmed ?? '—',
    events: summary?.total_events ?? '—'
  };

  if (!activeStore) {
    return <Alert variant="info">Select a store from the top bar to see its dashboard.</Alert>;
  }

  return (
    <>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h5 className="mb-0">Dashboard — {activeStore.name}</h5>
        <span className="badge bg-light-primary">Store: {activeStore.slug}</span>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" />
        </div>
      ) : (
        <>
          <Row>
            {STAT_CARDS.map((c) => (
              <Col key={c.key} md={6} xl={3}>
                <Card>
                  <Card.Body>
                    <div className="d-flex align-items-center">
                      <div className={`flex-shrink-0 me-3 text-${c.color}`}>
                        <i className="material-icons-two-tone" style={{ fontSize: 40 }}>
                          {c.icon}
                        </i>
                      </div>
                      <div className="flex-grow-1">
                        <h6 className="mb-1 text-muted">{c.label}</h6>
                        <h4 className="mb-0">{values[c.key]}</h4>
                      </div>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>

          <Row>
            <Col md={12}>
              <Card>
                <Card.Header>
                  <h5>Events by type</h5>
                </Card.Header>
                <Card.Body>
                  <Table responsive hover className="mb-0">
                    <thead>
                      <tr>
                        <th>Event</th>
                        <th className="text-end">Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(summary?.events || {}).length === 0 && (
                        <tr>
                          <td colSpan={2} className="text-center text-muted py-4">
                            No events recorded yet.
                          </td>
                        </tr>
                      )}
                      {Object.entries(summary?.events || {}).map(([name, n]) => (
                        <tr key={name}>
                          <td>{name}</td>
                          <td className="text-end">{n}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </>
  );
}
