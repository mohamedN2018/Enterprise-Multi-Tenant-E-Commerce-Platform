import { useCallback, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { Alert, Badge, Card, Col, Row, Spinner, Table } from 'react-bootstrap';
import Chart from 'react-apexcharts';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';
import { useStore } from 'contexts/StoreContext';

const STATUS_VARIANT = { confirmed: 'success', completed: 'success', pending: 'warning', cancelled: 'danger' };

function Kpi({ icon, color, label, value, sub }) {
  return (
    <Card className="h-100">
      <Card.Body>
        <div className="d-flex align-items-center">
          <div className={`flex-shrink-0 me-3 d-flex align-items-center justify-content-center rounded bg-light-${color} text-${color}`} style={{ width: 48, height: 48 }}>
            <FeatherIcon icon={icon} size={22} />
          </div>
          <div className="flex-grow-1">
            <h6 className="mb-1 text-muted">{label}</h6>
            <h4 className="mb-0">{value}</h4>
            {sub != null && <div className="small text-muted">{sub}</div>}
          </div>
        </div>
      </Card.Body>
    </Card>
  );
}

Kpi.propTypes = {
  icon: PropTypes.string,
  color: PropTypes.string,
  label: PropTypes.string,
  value: PropTypes.node,
  sub: PropTypes.node
};

export default function Overview() {
  const { activeStore } = useStore();
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const cur = activeStore?.currency || '';

  const load = useCallback(async () => {
    if (!activeStore) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      setD(await apiGet('/analytics/dashboard/'));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [activeStore]);

  useEffect(() => {
    load();
  }, [load]);

  const revenueChart = useMemo(() => {
    const series = d?.revenue_series || [];
    return {
      options: {
        chart: { type: 'area', toolbar: { show: false } },
        stroke: { curve: 'smooth', width: 2 },
        colors: ['#4f46e5'],
        fill: { type: 'gradient', gradient: { opacityFrom: 0.35, opacityTo: 0.05 } },
        dataLabels: { enabled: false },
        xaxis: { categories: series.map((p) => p.date.slice(5)) },
        grid: { borderColor: '#f0f0f0' },
        tooltip: { y: { formatter: (v) => `${v} ${cur}` } }
      },
      series: [{ name: 'Revenue', data: series.map((p) => Number(p.revenue)) }]
    };
  }, [d, cur]);

  const statusChart = useMemo(
    () => ({
      options: {
        chart: { type: 'donut' },
        labels: ['Confirmed', 'Pending', 'Cancelled'],
        colors: ['#2ca87f', '#e58a00', '#e5484d'],
        legend: { position: 'bottom' }
      },
      series: [d?.orders?.confirmed || 0, d?.orders?.pending || 0, d?.orders?.cancelled || 0]
    }),
    [d]
  );

  const eventNames = Object.keys(d?.events || {});
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
      series: [{ name: 'Events', data: eventNames.map((n) => d.events[n]) }]
    }),
    [d] // eslint-disable-line react-hooks/exhaustive-deps
  );

  if (!activeStore) return <Alert variant="info">Select a store from the top bar to see its dashboard.</Alert>;
  if (loading)
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
      </div>
    );
  if (error) return <Alert variant="danger">{error}</Alert>;

  const o = d?.orders || {};
  const cat = d?.catalog || {};
  const alerts = [
    { n: d?.reviews?.pending, label: 'reviews to moderate', to: '/admin/r/reviews', icon: 'star', color: 'warning' },
    { n: d?.returns_pending, label: 'returns to process', to: '/admin/r/returns', icon: 'corner-up-left', color: 'info' },
    { n: d?.fraud_pending, label: 'fraud checks pending', to: '/admin/r/fraud', icon: 'shield', color: 'danger' },
    { n: cat.low_stock, label: 'low-stock items', to: '/admin/r/stock', icon: 'alert-triangle', color: 'danger' }
  ].filter((a) => Number(a.n) > 0);

  return (
    <>
      <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
        <h5 className="mb-0">Dashboard — {activeStore.name}</h5>
        <span className="badge bg-light-primary">
          Wallet: {d?.payout_balance} {d?.payout_currency}
        </span>
      </div>

      <Row className="g-3 mb-1">
        <Col md={6} xl={3}>
          <Kpi icon="dollar-sign" color="success" label="Revenue (confirmed)" value={`${o.revenue} ${cur}`} sub={`AOV ${o.aov} ${cur}`} />
        </Col>
        <Col md={6} xl={3}>
          <Kpi icon="shopping-bag" color="primary" label="Orders" value={o.count} sub={`${o.confirmed} confirmed · ${o.pending} pending`} />
        </Col>
        <Col md={6} xl={3}>
          <Kpi icon="users" color="info" label="Customers" value={d?.customers ?? 0} />
        </Col>
        <Col md={6} xl={3}>
          <Kpi icon="box" color="warning" label="Products" value={cat.products} sub={`${cat.published} published · ${cat.categories} categories`} />
        </Col>
      </Row>
      <Row className="g-3 mb-4">
        <Col md={6} xl={3}>
          <Kpi icon="star" color="warning" label="Avg rating" value={d?.reviews?.average ?? 0} sub={`${d?.reviews?.pending ?? 0} pending`} />
        </Col>
        <Col md={6} xl={3}>
          <Kpi icon="alert-triangle" color="danger" label="Low stock" value={cat.low_stock} />
        </Col>
        <Col md={6} xl={3}>
          <Kpi icon="corner-up-left" color="info" label="Returns pending" value={d?.returns_pending ?? 0} />
        </Col>
        <Col md={6} xl={3}>
          <Kpi icon="activity" color="secondary" label="Tracked events" value={d?.total_events ?? 0} />
        </Col>
      </Row>

      {alerts.length > 0 && (
        <Row className="g-2 mb-4">
          {alerts.map((a) => (
            <Col md={6} xl={3} key={a.label}>
              <Card as={Link} to={a.to} className={`text-decoration-none border-${a.color}`}>
                <Card.Body className="py-2 d-flex align-items-center gap-2">
                  <span className={`text-${a.color}`}>
                    <FeatherIcon icon={a.icon} size={18} />
                  </span>
                  <span>
                    <strong>{a.n}</strong> {a.label} →
                  </span>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Row className="g-3 mb-4">
        <Col xl={8}>
          <Card className="h-100">
            <Card.Header>
              <h5 className="mb-0">Revenue — last 14 days</h5>
            </Card.Header>
            <Card.Body>
              <Chart options={revenueChart.options} series={revenueChart.series} type="area" height={280} />
            </Card.Body>
          </Card>
        </Col>
        <Col xl={4}>
          <Card className="h-100">
            <Card.Header>
              <h5 className="mb-0">Order status</h5>
            </Card.Header>
            <Card.Body>
              {o.count ? (
                <Chart options={statusChart.options} series={statusChart.series} type="donut" height={280} />
              ) : (
                <p className="text-muted text-center py-5 mb-0">No orders yet.</p>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="g-3">
        <Col xl={5}>
          <Card className="h-100">
            <Card.Header>
              <h5 className="mb-0">Top products</h5>
            </Card.Header>
            <Card.Body className="p-0">
              <Table responsive hover className="mb-0 align-middle">
                <thead>
                  <tr>
                    <th className="ps-3">Product</th>
                    <th className="text-end">Units</th>
                    <th className="text-end pe-3">Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {(d?.top_products || []).length === 0 && (
                    <tr>
                      <td colSpan={3} className="text-center text-muted py-4">No sales yet.</td>
                    </tr>
                  )}
                  {(d?.top_products || []).map((t) => (
                    <tr key={t.name}>
                      <td className="ps-3">{t.name}</td>
                      <td className="text-end">{t.units}</td>
                      <td className="text-end pe-3">{t.revenue} {cur}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
        <Col xl={7}>
          <Card className="h-100">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Recent orders</h5>
              <Link to="/admin/r/orders" className="small text-decoration-none">
                View all →
              </Link>
            </Card.Header>
            <Card.Body className="p-0">
              <Table responsive hover className="mb-0 align-middle">
                <thead>
                  <tr>
                    <th className="ps-3">Order</th>
                    <th>Status</th>
                    <th className="text-end">Total</th>
                    <th className="pe-3">Placed</th>
                  </tr>
                </thead>
                <tbody>
                  {(d?.recent_orders || []).length === 0 && (
                    <tr>
                      <td colSpan={4} className="text-center text-muted py-4">No orders yet.</td>
                    </tr>
                  )}
                  {(d?.recent_orders || []).map((r) => (
                    <tr key={r.number}>
                      <td className="ps-3 fw-semibold">{r.number}</td>
                      <td>
                        <Badge bg={STATUS_VARIANT[r.status] || 'secondary'}>{r.status}</Badge>
                      </td>
                      <td className="text-end">{r.total} {r.currency}</td>
                      <td className="pe-3">{r.created_at ? r.created_at.slice(0, 10) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {eventNames.length > 0 && (
        <Row className="g-3 mt-1">
          <Col xl={12}>
            <Card>
              <Card.Header>
                <h5 className="mb-0">Events by type</h5>
              </Card.Header>
              <Card.Body>
                <Chart options={eventsChart.options} series={eventsChart.series} type="bar" height={Math.max(200, eventNames.length * 40)} />
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </>
  );
}
