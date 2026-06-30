import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Card, Col, Row, Spinner } from 'react-bootstrap';
import Chart from 'react-apexcharts';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';
import { useStore } from 'contexts/StoreContext';

const STAT_CARDS = [
  { key: 'revenue', label: 'Revenue (confirmed)', icon: 'dollar-sign', color: 'success' },
  { key: 'count', label: 'Orders', icon: 'shopping-bag', color: 'primary' },
  { key: 'confirmed', label: 'Confirmed orders', icon: 'check-circle', color: 'info' },
  { key: 'events', label: 'Tracked events', icon: 'activity', color: 'warning' }
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
    revenue: summary ? `${summary.orders?.revenue ?? '0.00'} ${activeStore?.currency || ''}`.trim() : '—',
    count: summary?.orders?.count ?? '—',
    confirmed: summary?.orders?.confirmed ?? '—',
    events: summary?.total_events ?? '—'
  };

  const events = summary?.events || {};
  const eventNames = Object.keys(events);

  const eventsChart = useMemo(
    () => ({
      options: {
        chart: { type: 'bar', toolbar: { show: false } },
        plotOptions: { bar: { borderRadius: 4, horizontal: true, distributed: true } },
        legend: { show: false },
        dataLabels: { enabled: false },
        xaxis: { categories: eventNames.map((n) => n.replace(/_/g, ' ')) },
        grid: { borderColor: '#f0f0f0' }
      },
      series: [{ name: 'Events', data: eventNames.map((n) => events[n]) }]
    }),
    [summary] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const ordersCount = summary?.orders?.count || 0;
  const ordersConfirmed = summary?.orders?.confirmed || 0;
  const ordersChart = useMemo(
    () => ({
      options: {
        chart: { type: 'donut' },
        labels: ['Confirmed', 'Unconfirmed'],
        legend: { position: 'bottom' },
        colors: ['#2ca87f', '#e58a00'],
        dataLabels: { enabled: true }
      },
      series: [ordersConfirmed, Math.max(0, ordersCount - ordersConfirmed)]
    }),
    [summary] // eslint-disable-line react-hooks/exhaustive-deps
  );

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
                      <div className={`flex-shrink-0 me-3 d-flex align-items-center justify-content-center rounded bg-light-${c.color} text-${c.color}`} style={{ width: 52, height: 52 }}>
                        <FeatherIcon icon={c.icon} size={26} />
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
            <Col xl={8}>
              <Card>
                <Card.Header>
                  <h5>Events by type</h5>
                </Card.Header>
                <Card.Body>
                  {eventNames.length === 0 ? (
                    <p className="text-center text-muted py-5 mb-0">No events recorded yet.</p>
                  ) : (
                    <Chart options={eventsChart.options} series={eventsChart.series} type="bar" height={Math.max(220, eventNames.length * 38)} />
                  )}
                </Card.Body>
              </Card>
            </Col>
            <Col xl={4}>
              <Card>
                <Card.Header>
                  <h5>Order conversion</h5>
                </Card.Header>
                <Card.Body>
                  {ordersCount === 0 ? (
                    <p className="text-center text-muted py-5 mb-0">No orders yet.</p>
                  ) : (
                    <Chart options={ordersChart.options} series={ordersChart.series} type="donut" height={300} />
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </>
  );
}
