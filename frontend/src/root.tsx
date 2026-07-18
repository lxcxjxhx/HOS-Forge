import {
  Links,
  Meta,
  MetaFunction,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router";
import "./tailwind.css";
import "./index.css";
import React from "react";
import { Toaster } from "react-hot-toast";
import { useInvitation } from "#/hooks/use-invitation";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
        <Toaster />
        <div id="modal-portal-exit" />
      </body>
    </html>
  );
}

export const meta: MetaFunction = () => [
  { title: "HOS-Forge — AI Native Cyber Security IDE" },
  { name: "description", content: "HOS-Forge: AI Native Cyber Security IDE — 让 AI 成为安全工程师的协作伙伴" },
  { name: "theme-color", content: "#2D1A36" },
];

export default function App() {
  // Handle invitation token cleanup when invitation flow completes
  // This runs on all pages to catch redirects from auth callback
  useInvitation();

  return <Outlet />;
}
