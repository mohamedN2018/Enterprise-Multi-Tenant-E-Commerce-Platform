// Bilingual message catalog. Arabic is the default/base locale.
export default {
  ar: {
    common: {
      add: 'إضافة', edit: 'تعديل', delete: 'حذف', save: 'حفظ', cancel: 'إلغاء', create: 'إنشاء',
      close: 'إغلاق', search: 'بحث', view: 'عرض', all: 'الكل', back: 'رجوع', confirm: 'تأكيد',
      loading: 'جارٍ التحميل…', none: 'لا شيء', actions: '', status: 'الحالة', price: 'السعر',
      total: 'الإجمالي', subtotal: 'المجموع الفرعي', discount: 'الخصم', quantity: 'الكمية',
      remove: 'إزالة', apply: 'تطبيق', submit: 'إرسال', yes: 'نعم', no: 'لا', readOnly: 'للقراءة فقط',
      export: 'تصدير', refresh: 'تحديث', filters: 'الفلاتر', reset: 'إعادة تعيين', clear: 'مسح',
      selected: 'محدد', of: 'من', items: 'عناصر', date: 'التاريخ', name: 'الاسم', email: 'البريد الإلكتروني',
      phone: 'الهاتف', country: 'الدولة', city: 'المدينة', description: 'الوصف', type: 'النوع',
      active: 'مفعّل', inactive: 'غير مفعّل', more: 'المزيد', noResults: 'لا توجد نتائج'
    },
    nav: {
      home: 'الرئيسية', shop: 'المتجر', stores: 'المتاجر', account: 'حسابي', help: 'مساعدة',
      support: 'الدعم', contact: 'تواصل معنا', callUs: 'اتصل بنا', myAccount: 'حسابي',
      login: 'تسجيل الدخول', register: 'إنشاء حساب', logout: 'تسجيل الخروج', dashboard: 'لوحة التحكم',
      myCart: 'سلتي', allCategories: 'كل الأقسام', wishlist: 'المفضلة', compare: 'مقارنة',
      searchPlaceholder: 'ابحث عن منتج…', yourCart: 'سلتك', viewCart: 'عرض السلة', checkout: 'الدفع',
      cartEmpty: 'سلتك فارغة.', menu: 'القائمة', categories: 'الأقسام'
    },
    home: {
      heroBadge: 'أهلاً بك في q-shop', heroTitle: 'كل ما تحب، من', heroHighlight: 'متاجر مستقلة',
      heroSubtitle: 'تسوّق آلاف المنتجات في الإلكترونيات والأزياء والمنزل وأكثر — سلة واحدة، دفع آمن، وتوصيل سريع من بائعين موثوقين.',
      shopNow: 'تسوّق الآن', becomeSeller: 'كن بائعًا', stores: 'متجر', categories: 'قسم', support: 'دعم',
      shopByCategory: 'تسوّق حسب القسم', featuredStores: 'متاجر مميزة', viewAll: 'عرض الكل',
      recentlyViewed: 'شوهدت مؤخرًا', ourProducts: 'منتجاتنا', newArrivals: 'وصل حديثًا', onSale: 'عروض',
      viewAllProducts: 'عرض كل المنتجات', testimonials: 'ماذا يقول عملاؤنا', items: 'منتج',
      sellerCtaTitle: 'ابدأ البيع على q-shop اليوم', sellerCtaText: 'افتح متجرك، وصل لآلاف المتسوّقين، ونمِّ عملك.',
      independentStore: 'متجر مستقل', verifiedBuyer: 'مشترٍ موثّق',
      svc: {
        freeReturn: 'إرجاع مجاني', freeReturnMsg: 'ضمان استرداد المال خلال 30 يومًا!',
        freeShipping: 'شحن مجاني', freeShippingMsg: 'شحن مجاني على كل الطلبات',
        support: 'دعم 24/7', supportMsg: 'دعم أونلاين على مدار الساعة',
        gift: 'بطاقات هدايا', giftMsg: 'استلم هدية على الطلبات فوق 50$',
        secure: 'دفع آمن', secureMsg: 'نحرص على أمانك', online: 'خدمة أونلاين', onlineMsg: 'إرجاع مجاني خلال 30 يومًا'
      }
    },
    product: {
      addToCart: 'أضف للسلة', adding: 'جارٍ الإضافة…', outOfStock: 'غير متوفر', options: 'الخيارات',
      inStock: 'متوفر وجاهز للشحن', unavailable: 'غير متاح حاليًا', fastDelivery: 'توصيل سريع ومتتبَّع',
      securePayment: 'دفع آمن', description: 'الوصف', reviews: 'التقييمات', writeReview: 'اكتب تقييمًا',
      yourRating: 'تقييمك', reviewTitle: 'عنوان (اختياري)', reviewBody: 'شاركنا تجربتك…', submitReview: 'إرسال التقييم',
      signInToReview: 'سجّل الدخول', toWriteReview: 'لكتابة تقييم.', noReviews: 'لا توجد تقييمات بعد',
      noReviewsMsg: 'كن أول من يقيّم هذا المنتج بعد الشراء.', related: 'منتجات ذات صلة', verified: 'موثّق',
      sale: 'خصم', moreFromStore: 'المزيد من هذا المتجر', wishlist: 'حفظ في المفضلة',
      notFound: 'المنتج غير موجود', notFoundMsg: 'ربما تم حذف هذا المنتج أو لم يعد متاحًا.',
      browseProducts: 'تصفّح المنتجات', noDescription: 'لا يوجد وصف لهذا المنتج.'
    },
    shop: {
      title: 'المتجر', productsFound: 'منتج', categories: 'الأقسام', filter: 'تصفية', onSaleOnly: 'العروض فقط',
      resetFilters: 'إعادة تعيين كل الفلاتر', allProducts: 'كل المنتجات', noProducts: 'لا توجد منتجات',
      noProductsMsg: 'جرّب تعديل الفلاتر أو كلمات البحث.', clearFilters: 'مسح الفلاتر'
    },
    cart: {
      title: 'سلة التسوق', empty: 'سلتك فارغة', emptyMsg: 'تصفّح السوق وأضف المنتجات التي تحبها.',
      startShopping: 'ابدأ التسوق', signInTitle: 'سجّل الدخول لعرض سلتك',
      signInMsg: 'سلتك محفوظة في حسابك لتكمل من حيث توقفت.', orderSummary: 'ملخص الطلب',
      checkout: 'إتمام الدفع', continueShopping: 'مواصلة التسوق', coupon: 'كود الخصم', shoppingAt: 'تتسوّق من',
      each: 'للوحدة', couponApplied: 'تم تطبيق الكوبون.'
    },
    checkout: {
      title: 'الدفع', shippingAddress: 'عنوان الشحن', newAddress: 'عنوان جديد', shippingMethod: 'طريقة الشحن',
      free: 'مجاني', orderSummary: 'ملخص الطلب', placeOrder: 'تأكيد الطلب', secureCheckout: 'دفع آمن ومشفّر',
      fullName: 'الاسم الكامل', line1: 'العنوان 1', line2: 'العنوان 2', region: 'المنطقة/المحافظة',
      postal: 'الرمز البريدي', saveAddress: 'حفظ العنوان', preparing: 'جارٍ تجهيز الدفع…', emptyCart: 'سلتك فارغة',
      emptyCartMsg: 'أضف عناصر للسلة قبل إتمام الدفع.', browseProducts: 'تصفّح المنتجات', orderPlaced: 'تم تأكيد الطلب بنجاح!'
    },
    account: {
      title: 'حسابي', profile: 'الملف الشخصي', orders: 'الطلبات', returns: 'المرتجعات', addresses: 'العناوين',
      wishlist: 'المفضلة', downloads: 'التنزيلات', rewards: 'المكافآت', referrals: 'الإحالات', sessions: 'الجلسات',
      security: 'الأمان', settings: 'الإعدادات', signOut: 'تسجيل الخروج', memberSince: 'عضو منذ',
      accountType: 'نوع الحساب', customer: 'عميل', staff: 'موظف', verified: 'موثّق', unverified: 'غير موثّق',
      sellerDashboard: 'لوحة تحكم البائع', noOrders: 'لا توجد طلبات بعد', requestReturn: 'طلب إرجاع',
      changePassword: 'تغيير كلمة المرور', currentPassword: 'كلمة المرور الحالية', newPassword: 'كلمة المرور الجديدة',
      confirmPassword: 'تأكيد كلمة المرور', updatePassword: 'تحديث كلمة المرور', walletBalance: 'رصيد المحفظة',
      loyaltyPoints: 'نقاط الولاء', redeemGift: 'استبدال بطاقة هدية', redeemPoints: 'استبدال النقاط',
      language: 'اللغة', theme: 'المظهر', light: 'نهاري', dark: 'ليلي', arabic: 'العربية', english: 'الإنجليزية',
      preferences: 'التفضيلات', notifPrefs: 'تفضيلات الإشعارات', inApp: 'إشعارات داخل التطبيق', emailNotif: 'إشعارات بريدية',
      savePrefs: 'حفظ التفضيلات', activeSessions: 'الجلسات النشطة', signOutAll: 'تسجيل الخروج من الكل', revoke: 'إلغاء'
    },
    auth: {
      signIn: 'تسجيل الدخول', signInSubtitle: 'أهلاً بعودتك. من فضلك أدخل بياناتك.', password: 'كلمة المرور',
      forgotPassword: 'نسيت كلمة المرور؟', noAccount: 'ليس لديك حساب؟', createOne: 'أنشئ حسابًا',
      createAccount: 'أنشئ حسابك', registerSubtitle: 'ابدأ التسوق في دقائق.', confirmPassword: 'تأكيد كلمة المرور',
      alreadyHave: 'لديك حساب بالفعل؟', welcomeBack: 'أهلاً بعودتك!', accountCreated: 'تم إنشاء الحساب! سجّل الدخول من فضلك.',
      passwordsNoMatch: 'كلمتا المرور غير متطابقتين.'
    },
    footer: {
      about: 'q-shop — سوقك متعدد البائعين للإلكترونيات والأزياء والمنزل وأكثر، منتقاة من متاجر مستقلة موثوقة.',
      account: 'الحساب', myAccount: 'حسابي', orderHistory: 'سجل الطلبات', quickLinks: 'روابط سريعة',
      sellOn: 'بِع على q-shop', openStore: 'افتح متجرًا', newsletter: 'النشرة البريدية',
      newsletterMsg: 'اشترك للحصول على العروض والوصول الجديد.', yourEmail: 'بريدك الإلكتروني',
      rights: '© 2026 q-shop. جميع الحقوق محفوظة.', builtOn: 'مبني على منصة متعددة المستأجرين للمؤسسات.'
    },
    status: {
      pending: 'قيد الانتظار', confirmed: 'مؤكد', cancelled: 'ملغي', canceled: 'ملغي', completed: 'مكتمل',
      delivered: 'تم التسليم', shipped: 'تم الشحن', processing: 'قيد المعالجة', paid: 'مدفوع', failed: 'فشل',
      refunded: 'مسترد', approved: 'معتمد', rejected: 'مرفوض', active: 'مفعّل', inactive: 'غير مفعّل',
      draft: 'مسودة', published: 'منشور', archived: 'مؤرشف', requested: 'مطلوب', suspended: 'موقوف'
    },
    roles: { platform: 'مدير المنصة', owner: 'مالك', manager: 'مدير', employee: 'موظف', member: 'عضو' },
    admin: {
      overview: 'نظرة عامة', catalog: 'الكتالوج', sales: 'المبيعات', marketing: 'التسويق',
      operations: 'العمليات', finance: 'المالية', store: 'المتجر', dashboard: 'لوحة التحكم',
      analytics: 'التحليلات', platform: 'المنصة', products: 'المنتجات', categories: 'الأقسام', brands: 'العلامات',
      attributes: 'الخصائص', orders: 'الطلبات', returns: 'المرتجعات', payments: 'المدفوعات', reviews: 'التقييمات',
      promotions: 'العروض', campaigns: 'الحملات', giftCards: 'بطاقات الهدايا', inventory: 'المخزون',
      shipping: 'الشحن', procurement: 'المشتريات', pricing: 'التسعير', fraud: 'الاحتيال', payouts: 'المدفوعات المستحقة',
      notifications: 'الإشعارات', team: 'الفريق', settings: 'الإعدادات', seller: 'بائع', admin: 'مدير',
      viewStorefront: 'عرض الواجهة', selectStore: 'اختر متجرًا', noStores: 'لا توجد متاجر بعد'
    }
  },
  en: {
    common: {
      add: 'Add', edit: 'Edit', delete: 'Delete', save: 'Save', cancel: 'Cancel', create: 'Create',
      close: 'Close', search: 'Search', view: 'View', all: 'All', back: 'Back', confirm: 'Confirm',
      loading: 'Loading…', none: 'None', actions: '', status: 'Status', price: 'Price', total: 'Total',
      subtotal: 'Subtotal', discount: 'Discount', quantity: 'Quantity', remove: 'Remove', apply: 'Apply',
      submit: 'Submit', yes: 'Yes', no: 'No', readOnly: 'Read-only', export: 'Export', refresh: 'Refresh',
      filters: 'Filters', reset: 'Reset', clear: 'Clear', selected: 'selected', of: 'of', items: 'items',
      date: 'Date', name: 'Name', email: 'Email', phone: 'Phone', country: 'Country', city: 'City',
      description: 'Description', type: 'Type', active: 'Active', inactive: 'Inactive', more: 'More', noResults: 'No results'
    },
    nav: {
      home: 'Home', shop: 'Shop', stores: 'Stores', account: 'Account', help: 'Help', support: 'Support',
      contact: 'Contact', callUs: 'Call Us', myAccount: 'My Account', login: 'Login', register: 'Register',
      logout: 'Log Out', dashboard: 'Dashboard', myCart: 'My Cart', allCategories: 'All Categories',
      wishlist: 'Wishlist', compare: 'Compare', searchPlaceholder: 'Search Looking For?', yourCart: 'Your cart',
      viewCart: 'View cart', checkout: 'Checkout', cartEmpty: 'Your cart is empty.', menu: 'Menu', categories: 'Categories'
    },
    home: {
      heroBadge: 'Welcome to q-shop', heroTitle: 'Everything you love, from', heroHighlight: 'independent stores',
      heroSubtitle: 'Shop thousands of products across electronics, fashion, home and more — one cart, secure checkout, and fast delivery from verified sellers.',
      shopNow: 'Shop now', becomeSeller: 'Become a seller', stores: 'Stores', categories: 'Categories', support: 'Support',
      shopByCategory: 'Shop by Category', featuredStores: 'Featured Stores', viewAll: 'View all',
      recentlyViewed: 'Recently Viewed', ourProducts: 'Our Products', newArrivals: 'New Arrivals', onSale: 'On Sale',
      viewAllProducts: 'View all products', testimonials: 'What our customers say', items: 'items',
      sellerCtaTitle: 'Start selling on q-shop today', sellerCtaText: 'Open your store, reach thousands of shoppers, and grow your business.',
      independentStore: 'Independent store', verifiedBuyer: 'Verified buyer',
      svc: {
        freeReturn: 'Free Return', freeReturnMsg: '30 days money back guarantee!',
        freeShipping: 'Free Shipping', freeShippingMsg: 'Free shipping on all orders',
        support: 'Support 24/7', supportMsg: 'We support online 24 hrs a day',
        gift: 'Gift Cards', giftMsg: 'Receive a gift on orders over $50',
        secure: 'Secure Payment', secureMsg: 'We value your security', online: 'Online Service', onlineMsg: 'Free returns within 30 days'
      }
    },
    product: {
      addToCart: 'Add to cart', adding: 'Adding…', outOfStock: 'Out of stock', options: 'Options',
      inStock: 'In stock and ready to ship', unavailable: 'Currently unavailable', fastDelivery: 'Fast, tracked delivery',
      securePayment: 'Secure payment', description: 'Description', reviews: 'Reviews', writeReview: 'Write a review',
      yourRating: 'Your rating', reviewTitle: 'Title (optional)', reviewBody: 'Share your experience…', submitReview: 'Submit review',
      signInToReview: 'Sign in', toWriteReview: 'to write a review.', noReviews: 'No reviews yet',
      noReviewsMsg: 'Be the first to review this product after purchase.', related: 'Related Products', verified: 'Verified',
      sale: 'Sale', moreFromStore: 'More from this store', wishlist: 'Save to wishlist',
      notFound: 'Product not found', notFoundMsg: 'This product may have been removed or is no longer available.',
      browseProducts: 'Browse products', noDescription: 'No description provided for this product.'
    },
    shop: {
      title: 'Shop', productsFound: 'products found', categories: 'Categories', filter: 'Filter', onSaleOnly: 'On sale only',
      resetFilters: 'Reset all filters', allProducts: 'All Products', noProducts: 'No products found',
      noProductsMsg: 'Try adjusting your filters or search terms.', clearFilters: 'Clear filters'
    },
    cart: {
      title: 'Shopping Cart', empty: 'Your cart is empty', emptyMsg: 'Browse the marketplace and add products you love.',
      startShopping: 'Start shopping', signInTitle: 'Sign in to view your cart',
      signInMsg: 'Your cart is saved to your account so you can pick up where you left off.', orderSummary: 'Order summary',
      checkout: 'Checkout', continueShopping: 'Continue shopping', coupon: 'Coupon code', shoppingAt: 'Shopping at',
      each: 'each', couponApplied: 'Coupon applied.'
    },
    checkout: {
      title: 'Checkout', shippingAddress: 'Shipping address', newAddress: 'New address', shippingMethod: 'Shipping method',
      free: 'Free', orderSummary: 'Order summary', placeOrder: 'Place order', secureCheckout: 'Secure, encrypted checkout',
      fullName: 'Full name', line1: 'Address line 1', line2: 'Address line 2', region: 'State / Region',
      postal: 'Postal code', saveAddress: 'Save address', preparing: 'Preparing checkout…', emptyCart: 'Your cart is empty',
      emptyCartMsg: 'Add items to your cart before checking out.', browseProducts: 'Browse products', orderPlaced: 'Order placed successfully!'
    },
    account: {
      title: 'My account', profile: 'Profile', orders: 'Orders', returns: 'Returns', addresses: 'Addresses',
      wishlist: 'Wishlist', downloads: 'Downloads', rewards: 'Rewards', referrals: 'Referrals', sessions: 'Sessions',
      security: 'Security', settings: 'Settings', signOut: 'Sign out', memberSince: 'Member since',
      accountType: 'Account type', customer: 'Customer', staff: 'Staff', verified: 'Verified', unverified: 'Unverified',
      sellerDashboard: 'Seller dashboard', noOrders: 'No orders yet', requestReturn: 'Request return',
      changePassword: 'Change password', currentPassword: 'Current password', newPassword: 'New password',
      confirmPassword: 'Confirm new password', updatePassword: 'Update password', walletBalance: 'Wallet balance',
      loyaltyPoints: 'Loyalty points', redeemGift: 'Redeem gift card', redeemPoints: 'Redeem points',
      language: 'Language', theme: 'Theme', light: 'Light', dark: 'Dark', arabic: 'Arabic', english: 'English',
      preferences: 'Preferences', notifPrefs: 'Notification preferences', inApp: 'In-app notifications', emailNotif: 'Email notifications',
      savePrefs: 'Save preferences', activeSessions: 'Active sessions', signOutAll: 'Sign out all', revoke: 'Revoke'
    },
    auth: {
      signIn: 'Sign in', signInSubtitle: 'Welcome back. Please enter your details.', password: 'Password',
      forgotPassword: 'Forgot password?', noAccount: "Don't have an account?", createOne: 'Create one',
      createAccount: 'Create your account', registerSubtitle: 'Start shopping in minutes.', confirmPassword: 'Confirm password',
      alreadyHave: 'Already have an account?', welcomeBack: 'Welcome back!', accountCreated: 'Account created! Please sign in.',
      passwordsNoMatch: 'Passwords do not match.'
    },
    footer: {
      about: 'q-shop — your multi-vendor marketplace for electronics, fashion, home and more, curated from verified independent stores.',
      account: 'Account', myAccount: 'My Account', orderHistory: 'Order History', quickLinks: 'Quick Links',
      sellOn: 'Sell on q-shop', openStore: 'Open a Store', newsletter: 'Newsletter',
      newsletterMsg: 'Subscribe for deals and new arrivals.', yourEmail: 'Your email',
      rights: '© 2026 q-shop. All rights reserved.', builtOn: 'Built on an enterprise multi-tenant platform.'
    },
    status: {
      pending: 'Pending', confirmed: 'Confirmed', cancelled: 'Cancelled', canceled: 'Cancelled', completed: 'Completed',
      delivered: 'Delivered', shipped: 'Shipped', processing: 'Processing', paid: 'Paid', failed: 'Failed',
      refunded: 'Refunded', approved: 'Approved', rejected: 'Rejected', active: 'Active', inactive: 'Inactive',
      draft: 'Draft', published: 'Published', archived: 'Archived', requested: 'Requested', suspended: 'Suspended'
    },
    roles: { platform: 'Platform Admin', owner: 'Owner', manager: 'Manager', employee: 'Employee', member: 'Member' },
    admin: {
      overview: 'Overview', catalog: 'Catalog', sales: 'Sales', marketing: 'Marketing', operations: 'Operations',
      finance: 'Finance', store: 'Store', dashboard: 'Dashboard', analytics: 'Analytics', platform: 'Platform',
      products: 'Products', categories: 'Categories', brands: 'Brands', attributes: 'Attributes', orders: 'Orders',
      returns: 'Returns', payments: 'Payments', reviews: 'Reviews', promotions: 'Promotions', campaigns: 'Campaigns',
      giftCards: 'Gift cards', inventory: 'Inventory', shipping: 'Shipping', procurement: 'Procurement', pricing: 'Pricing',
      fraud: 'Fraud', payouts: 'Payouts', notifications: 'Notifications', team: 'Team', settings: 'Settings',
      seller: 'Seller', admin: 'Admin', viewStorefront: 'View storefront', selectStore: 'Select store', noStores: 'No stores yet'
    }
  }
};
