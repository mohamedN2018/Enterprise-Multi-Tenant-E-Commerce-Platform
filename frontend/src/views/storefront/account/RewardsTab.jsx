import { useCallback, useEffect, useState } from 'react';
import { Alert, Button, Card, Col, Form, InputGroup, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import api, { errorMessage } from 'api/client';

export default function RewardsTab({ store }) {
  const [wallet, setWallet] = useState(null);
  const [loyalty, setLoyalty] = useState(null);
  const [referral, setReferral] = useState(null);
  const [loading, setLoading] = useState(true);
  const [gift, setGift] = useState('');
  const [refCode, setRefCode] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const currency = store?.currency || '';
  const headers = { 'X-Store-Id': store.id };

  const load = useCallback(async () => {
    setLoading(true);
    const get = (url) => api.get(url, { headers }).then((r) => r.data).catch(() => null);
    const [w, l, r] = await Promise.all([get('/rewards/wallet/'), get('/rewards/loyalty/'), get('/rewards/referrals/code/')]);
    setWallet(w);
    setLoyalty(l);
    setReferral(r);
    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.id]);

  useEffect(() => {
    load();
  }, [load]);

  const act = async (fn, success) => {
    setError('');
    setNotice('');
    try {
      await fn();
      setNotice(success);
      load();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  if (loading) return <div className="text-center py-5"><Spinner animation="border" variant="primary" /></div>;

  const refStats = referral || {};
  const referralCode = refStats.code || refStats.referral_code || '';

  return (
    <>
      {notice && <Alert variant="success" className="py-2">{notice}</Alert>}
      {error && <Alert variant="danger" className="py-2">{error}</Alert>}
      <Row className="g-3">
        <Col md={6}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small">Wallet balance</div>
              <div className="display-6 fw-bold text-primary">
                {wallet?.balance ?? '0.00'} {wallet?.currency || currency}
              </div>
              <Form
                className="mt-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (gift.trim()) act(() => api.post('/rewards/gift-cards/redeem/', { code: gift.trim() }, { headers }), 'Gift card redeemed to your wallet.').then(() => setGift(''));
                }}
              >
                <Form.Label className="small">Redeem a gift card</Form.Label>
                <InputGroup size="sm">
                  <Form.Control placeholder="Gift card code" value={gift} onChange={(e) => setGift(e.target.value)} />
                  <Button type="submit" variant="outline-primary">Redeem</Button>
                </InputGroup>
              </Form>
              {(wallet?.transactions || []).length > 0 && (
                <div className="mt-3 small">
                  <div className="text-muted mb-1">Recent activity</div>
                  {(wallet.transactions || []).slice(0, 4).map((t) => (
                    <div key={t.id} className="d-flex justify-content-between border-bottom py-1">
                      <span>{t.reason || t.txn_type}</span>
                      <span className={Number(t.amount) < 0 ? 'text-danger' : 'text-success'}>
                        {t.amount} {currency}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small">Loyalty points</div>
              <div className="display-6 fw-bold text-warning">
                <FeatherIcon icon="award" size={28} className="me-1" />
                {loyalty?.points ?? 0}
              </div>
              <Form
                className="mt-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  const pts = Number(e.target.elements.pts.value);
                  if (pts > 0) act(() => api.post('/rewards/loyalty/redeem/', { points: pts }, { headers }), 'Points redeemed to wallet credit.');
                }}
              >
                <Form.Label className="small">Redeem points for wallet credit</Form.Label>
                <InputGroup size="sm">
                  <Form.Control name="pts" type="number" min={1} placeholder="Points" />
                  <Button type="submit" variant="outline-warning">Redeem</Button>
                </InputGroup>
              </Form>

              <hr />
              <div className="text-muted small">Your referral code</div>
              {referralCode ? (
                <div className="fw-bold fs-5">{referralCode}</div>
              ) : (
                <div className="text-muted small">Not available.</div>
              )}
              <Form
                className="mt-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (refCode.trim()) act(() => api.post('/rewards/referrals/apply/', { code: refCode.trim() }, { headers }), 'Referral code applied.').then(() => setRefCode(''));
                }}
              >
                <Form.Label className="small">Have a friend&apos;s code?</Form.Label>
                <InputGroup size="sm">
                  <Form.Control placeholder="Referral code" value={refCode} onChange={(e) => setRefCode(e.target.value)} />
                  <Button type="submit" variant="outline-secondary">Apply</Button>
                </InputGroup>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
}
