import React from "react";
import HeaderNav from "./header-nav";

// Server component wrapper: keeps the usePathname hook inside a client
// component rendered by the root layout, avoiding static-render bailout.
function Header() {
    return <HeaderNav />;
}

export default Header;
