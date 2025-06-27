"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/strategies", label: "Strategies" },
  { href: "/analytics", label: "Analytics" },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-thin">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-14">
          <div className="flex items-center">
            <h1 className="text-lg font-light tracking-widest uppercase mr-12">
              elPyFi
            </h1>
            <div className="hidden sm:flex sm:space-x-8 h-full">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    "inline-flex items-center text-xs uppercase tracking-wider font-medium transition-colors h-full border-b-2",
                    pathname === item.href
                      ? "border-accent text-white"
                      : "border-transparent text-muted hover:text-white"
                  )}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center">
            <div className="text-xs uppercase tracking-wider">
              <span className="text-muted">PDT</span>
              <span className="ml-3 text-green-400">●</span>
              <span className="ml-1 text-green-400">Active</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}