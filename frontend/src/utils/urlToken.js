// Auth emails deliver one-time tokens in the URL *fragment* (#token=…) so the
// token is never sent to a server or leaked via the Referer header. Read it from
// the hash, falling back to the query string for older links / manual entry.
export function tokenFromUrl(route) {
  const hash = (route?.hash || '').replace(/^#/, '');
  const fromHash = new URLSearchParams(hash).get('token');
  return fromHash || route?.query?.token || '';
}
