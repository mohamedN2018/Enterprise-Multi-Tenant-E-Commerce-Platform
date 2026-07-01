// Sidebar menu, generated from the backend resource registry.
import { RESOURCE_GROUPS } from 'config/resources';

const menuItems = {
  items: [
    {
      id: 'navigation',
      title: 'Navigation',
      type: 'group',
      icon: 'icon-navigation',
      children: [
        {
          id: 'dashboard',
          title: 'Dashboard',
          type: 'item',
          icon: 'material-icons-two-tone',
          iconname: 'dashboard',
          url: '/admin'
        }
      ]
    },
    {
      id: 'manage',
      title: 'Manage',
      subtitle: 'Store operations',
      type: 'group',
      icon: 'icon-group',
      children: RESOURCE_GROUPS.map((group) => ({
        id: group.id,
        title: group.title,
        type: 'collapse',
        icon: 'material-icons-two-tone',
        iconname: group.iconname,
        children: group.resources.map((resource) => ({
          id: resource.key,
          title: resource.label,
          type: 'item',
          url: `/admin/r/${resource.key}`
        }))
      }))
    }
  ]
};

export default menuItems;
