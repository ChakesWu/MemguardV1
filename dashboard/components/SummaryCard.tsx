'use client'

export default function SummaryCard() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 pb-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Compliance Case Summary</h2>
        <p className="text-gray-500 mt-1">Scenario 02: Structuring Detection</p>
      </div>

      {/* Case Details */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div>
          <div className="text-sm text-gray-500">Case ID</div>
          <div className="text-lg font-semibold mt-1">TXN-2024-071001</div>
        </div>
        <div>
          <div className="text-sm text-gray-500">Amount</div>
          <div className="text-lg font-semibold mt-1">HKD 1,470,000</div>
        </div>
        <div>
          <div className="text-sm text-gray-500">Risk Assessment</div>
          <div className="text-lg font-bold text-red-600 mt-1">CRITICAL (0.93)</div>
        </div>
        <div>
          <div className="text-sm text-gray-500">Decision</div>
          <div className="text-lg font-bold text-red-600 mt-1">FILE SAR</div>
        </div>
      </div>

      {/* Key Findings */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Key Findings</h3>
        <ul className="space-y-3">
          <li className="flex items-start">
            <span className="text-red-500 mr-3 mt-1">•</span>
            <span className="text-gray-700">Customer split HKD 1.47M into 3 transactions to avoid HKD 500K reporting threshold</span>
          </li>
          <li className="flex items-start">
            <span className="text-red-500 mr-3 mt-1">•</span>
            <span className="text-gray-700">Pattern matches historical case SAR-2024-0033 (88% similarity)</span>
          </li>
          <li className="flex items-start">
            <span className="text-red-500 mr-3 mt-1">•</span>
            <span className="text-gray-700">Violates HKMA §35 reporting requirements</span>
          </li>
          <li className="flex items-start">
            <span className="text-red-500 mr-3 mt-1">•</span>
            <span className="text-gray-700">Multiple rapid transactions across jurisdictions (HK → Cayman → BVI)</span>
          </li>
        </ul>
      </div>

      {/* AI Performance */}
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">AI System Performance</h3>
        <div className="grid grid-cols-3 gap-6">
          <div>
            <div className="text-3xl font-bold text-purple-600">11</div>
            <div className="text-sm text-gray-600 mt-1">Memory Operations</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600">4</div>
            <div className="text-sm text-gray-600 mt-1">Agents Coordinated</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600">6.7s</div>
            <div className="text-sm text-gray-600 mt-1">Analysis Time</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600">5</div>
            <div className="text-sm text-gray-600 mt-1">Memory Types</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600">100%</div>
            <div className="text-sm text-gray-600 mt-1">Decision Transparency</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600">0.92</div>
            <div className="text-sm text-gray-600 mt-1">Confidence Score</div>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-500">Status</div>
            <div className="text-lg font-semibold text-amber-600 mt-1">Awaiting Human Review</div>
          </div>
          <button className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium">
            View Full Report
          </button>
        </div>
      </div>
    </div>
  )
}
