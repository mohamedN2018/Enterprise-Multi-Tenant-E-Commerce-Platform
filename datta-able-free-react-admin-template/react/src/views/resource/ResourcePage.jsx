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

  if (!activeStore) {
    return <Alert variant="info">Select a store from the top bar to view {resource.label}.</Alert>;
  }

  return (
    <Row>
      <Col sm={12}>
        <ResourceTable resource={resource} />
      </Col>
    </Row>
  );
}
