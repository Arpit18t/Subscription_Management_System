"use client";

import { useState } from "react";
import { useEffect } from "react";
const API_URL = "http://127.0.0.1:8000";

const subscriptions = [
{ name: "Netflix Premium", plan: "Monthly", price: "₹649", status: "Active" },
{ name: "Spotify Premium", plan: "Monthly", price: "₹119", status: "Active" },
{ name: "Microsoft 365", plan: "Yearly", price: "₹4,899", status: "Active" },
];

const invoices = [
{ id: "INV-1001", customer: "Aarav Sharma", amount: "₹1,299", status: "Paid" },
{ id: "INV-1002", customer: "Priya Verma", amount: "₹899", status: "Pending" },
{ id: "INV-1003", customer: "Rahul Singh", amount: "₹2,499", status: "Overdue" },
{ id: "INV-1004", customer: "Ananya Gupta", amount: "₹649", status: "Paid" },
];

export default function Home() {
const [realSubscriptions, setRealSubscriptions] = useState<any[]>([]);
const [token, setToken] = useState("");
const [email, setEmail] = useState("testcustomer@example.com");
const [password, setPassword] = useState("");
const [loginMessage, setLoginMessage] = useState("");
const [apiMessage, setApiMessage] = useState("Loading subscriptions...");

async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
  event.preventDefault();
  setLoginMessage("Logging in...");

  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });

    const data = await response.json();

    if (!response.ok) {
      setLoginMessage("Login failed. Check your email and password.");
      return;
    }

    setToken(data.access_token);
    setLoginMessage("Login successful!");
  } catch {
    setLoginMessage("Cannot connect to the backend.");
  }
}


useEffect(() => {
  fetch(`${API_URL}/portal/subscriptions`)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      setRealSubscriptions(Array.isArray(data) ? data : [data]);
      setApiMessage("Connected to backend");
    })
    .catch(() => {
      setApiMessage("Could not load subscriptions");
    });
}, []);
const [activeTab, setActiveTab] = useState("Overview");
const [filter, setFilter] = useState("All");

const filteredInvoices = invoices.filter(
(invoice) => filter === "All" || invoice.status === filter
);

return (
  {!token && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4">
    <form
      onSubmit={handleLogin}
      className="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl"
    >
      <h2 className="text-2xl font-bold text-slate-900">
        Welcome to SubscriptIQ
      </h2>

      <p className="mb-6 mt-2 text-sm text-slate-500">
        Login to access your subscription portal.
      </p>

      <label className="mb-2 block text-sm font-medium">Email</label>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        className="mb-4 w-full rounded-xl border border-slate-300 p-3"
        placeholder="Enter your email"
      />

      <label className="mb-2 block text-sm font-medium">Password</label>
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        className="mb-4 w-full rounded-xl border border-slate-300 p-3"
        placeholder="Enter your password"
      />

      <button
        type="submit"
        className="w-full rounded-xl bg-indigo-600 p-3 font-semibold text-white hover:bg-indigo-700"
      >
        Login
      </button>

      {loginMessage && (
        <p className="mt-4 text-sm text-slate-600">{loginMessage}</p>
      )}
    </form>
  </div>
)}
<main className="min-h-screen bg-slate-100 text-slate-800 md:flex">
<aside className="bg-slate-950 p-6 text-white md:min-h-screen md:w-64">
<h1 className="mb-2 text-2xl font-bold">Subscript<span className="text-indigo-400">IQ</span></h1>
<p className="mb-8 text-sm text-slate-400">Subscription Management</p>

    <p className="mb-3 text-xs uppercase tracking-widest text-slate-500">Workspace</p>

    {["Overview", "Customer Portal", "Subscriptions", "Invoices", "Finance"].map((tab) => (
      <button
        key={tab}
        onClick={() => setActiveTab(tab)}
        className={`mb-2 w-full rounded-xl px-4 py-3 text-left transition ${
          activeTab === tab
            ? "bg-indigo-600 text-white"
            : "text-slate-300 hover:bg-slate-800"
        }`}
      >
        {tab === "Overview" ? "▦" : tab === "Customer Portal" ? "♙" : tab === "Subscriptions" ? "◈" : tab === "Invoices" ? "▤" : "↗"}{" "}
        {tab}
      </button>
    ))}

    <div className="mt-12 rounded-2xl bg-slate-900 p-4">
      <p className="font-semibold">Need assistance?</p>
      <p className="mt-2 text-sm text-slate-400">Manage your subscriptions and billing from one place.</p>
    </div>
  </aside>

  <section className="min-w-0 flex-1 p-5 md:p-9">
    <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="text-sm text-slate-500">Workspace / {activeTab}</p>
        <h2 className="mt-1 text-3xl font-bold">{activeTab}</h2>
        <p className="mt-2 text-slate-500">Welcome back! Here is your subscription overview.</p>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <span className="mr-2 inline-block h-2 w-2 rounded-full bg-green-500"></span>
        System dashboard
      </div>
    </header>

    {activeTab === "Overview" || activeTab === "Finance" ? (
      <>
        <div className="mb-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {[
            { label: "Monthly Recurring Revenue", value: "₹2,48,500", note: "+12.8% this month", icon: "₹" },
            { label: "Annual Recurring Revenue", value: "₹29,82,000", note: "Projected annual revenue", icon: "↗" },
            { label: "Active Subscriptions", value: "1,284", note: "+8.2% this month", icon: "◈" },
            { label: "Outstanding Revenue", value: "₹18,450", note: "Requires attention", icon: "!" },
          ].map((item) => (
            <div key={item.label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">{item.label}</p>
                <span className="rounded-xl bg-indigo-50 px-3 py-2 font-bold text-indigo-600">{item.icon}</span>
              </div>
              <h3 className="mt-5 text-2xl font-bold">{item.value}</h3>
              <p className="mt-2 text-xs text-slate-500">{item.note}</p>
            </div>
          ))}
        </div>

        <div className="mb-8 grid gap-6 xl:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 xl:col-span-2">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-bold">Revenue Overview</h3>
                <p className="mt-1 text-sm text-slate-500">Illustrative monthly revenue trend</p>
              </div>
              <span className="rounded-lg bg-green-50 px-3 py-2 text-sm font-semibold text-green-700">↑ 12.8%</span>
            </div>

            <div className="mt-8 flex h-48 items-end justify-around gap-3 border-b border-slate-100 pb-2">
              {[42, 58, 47, 72, 62, 84, 70, 95, 77, 100, 86, 93].map((height, index) => (
                <div key={index} className="flex h-full flex-1 flex-col justify-end">
                  <div
                    title={`Month ${index + 1}: illustrative`}
                    style={{ height: `${height}%` }}
                    className="w-full rounded-t-md bg-indigo-500 transition hover:bg-indigo-700"
                  />
                </div>
              ))}
            </div>
            <div className="mt-3 flex justify-between text-xs text-slate-400">
              <span>Jan</span><span>Mar</span><span>May</span><span>Jul</span><span>Sep</span><span>Dec</span>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <h3 className="text-lg font-bold">Payment Summary</h3>
            <p className="mt-1 text-sm text-slate-500">Illustrative invoice breakdown</p>
            <div className="my-7 flex justify-center">
              <div className="flex h-36 w-36 items-center justify-center rounded-full border-[18px] border-indigo-500">
                <div className="text-center">
                  <p className="text-2xl font-bold">78%</p>
                  <p className="text-xs text-slate-500">Collected</p>
                </div>
              </div>
            </div>
            <div className="space-y-4 text-sm">
              <p className="flex justify-between"><span>Paid invoices</span><b className="text-green-600">78%</b></p>
              <p className="flex justify-between"><span>Pending invoices</span><b className="text-amber-600">14%</b></p>
              <p className="flex justify-between"><span>Overdue invoices</span><b className="text-red-600">8%</b></p>
            </div>
          </div>
        </div>
      </>
    ) : null}

    {activeTab === "Customer Portal" || activeTab === "Subscriptions" ? (
      <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-6">
        <div className="mb-5">
          <h3 className="text-lg font-bold">My Subscriptions</h3>
          <p className="mt-1 text-sm text-slate-500">Sample subscription records for the portal preview.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr><th className="p-3">Subscription</th><th className="p-3">Billing</th><th className="p-3">Price</th><th className="p-3">Status</th></tr>
            </thead>
            <tbody>
              {realSubscriptions.map((sub) => (
                <tr key={sub.plan_name} className="border-b border-slate-100">
                  <td className="p-3 font-semibold">{sub.name}</td>
                  <td className="p-3">{sub.billing_cycle}</td>
                  <td className="p-3">{sub.amount}</td>
                  <td className="p-3"><span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">{sub.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    ) : null}

    {activeTab === "Overview" || activeTab === "Invoices" || activeTab === "Finance" ? (
      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold">Recent Invoices</h3>
            <p className="mt-1 text-sm text-slate-500">View payments and identify overdue invoices.</p>
          </div>
          <select
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm outline-none focus:border-indigo-500"
          >
            <option value="All">All invoices</option>
            <option value="Paid">Paid</option>
            <option value="Pending">Pending</option>
            <option value="Overdue">Overdue</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr><th className="p-3">Invoice ID</th><th className="p-3">Customer</th><th className="p-3">Amount</th><th className="p-3">Status</th></tr>
            </thead>
            <tbody>
              {filteredInvoices.map((invoice) => (
                <tr key={invoice.id} className="border-b border-slate-100 last:border-0">
                  <td className="p-3 font-semibold">{invoice.id}</td>
                  <td className="p-3">{invoice.customer}</td>
                  <td className="p-3">{invoice.amount}</td>
                  <td className="p-3">
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      invoice.status === "Paid"
                        ? "bg-green-50 text-green-700"
                        : invoice.status === "Overdue"
                        ? "bg-red-50 text-red-700"
                        : "bg-amber-50 text-amber-700"
                    }`}>{invoice.status}</span>
                  </td>
                </tr>
              ))}
              {filteredInvoices.length === 0 ? (
                <tr><td colSpan={4} className="p-6 text-center text-slate-500">No invoices found.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    ) : null}

    <footer className="mt-8 text-center text-xs text-slate-400">
      SubscriptIQ · Subscription Management System · Dashboard preview
    </footer>
  </section>
</main>
</>
);
}