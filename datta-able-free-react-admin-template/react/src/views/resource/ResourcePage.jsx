import { useParams } from 'react-router-dom';
import { Alert, Col, Row } from 'react-bootstrap';

import ResourceTable from 'components/ResourceTable';
import { findResource } from 'config/resources';
import { useStore } from 'contexts/StoreContext';

export default function ResourcePage() {
  const { key } = useParams();
  const resource = findResource(key);
  const { activeStore } = useStore();

  if (!resource) {
    return <Alert variant="warning">Unknown resource: {key}</Alert>;
  }

  return (
    <Row>
      <Col sm={12}>
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h5 className="mb-0">{resource.label}</h5>
          {activeStore && <span className="badge bg-light-primary">{activeStore.name}</span>}
        </div>
        {!activeStore ? (
          <Alert variant="info">Select a store from the top bar to view {resource.label}.</Alert>
        ) : (
          <ResourceTable endpoint={resource.endpoint} columns={resource.columns} />
        )}
      </Col>
    </Row>
  );
}
