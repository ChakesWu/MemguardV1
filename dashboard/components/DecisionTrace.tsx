'use client'

export default function DecisionTrace() {
  // Mock data for demo
  const mockTrace = {
    input_influences: [
      { memory_key: 'sar_cases', memory_type: 'episodic', influence_score: 0.88, content_preview: 'SAR-2024-0033: Customer structured HKD 1.2M across...', similarity: 0.88 },
      { memory_key: 'regulations', memory_type: 'semantic', influence_score: 0.76, content_preview: 'HKMA §35: Financial institutions must file STR for...', similarity: 0.91 },
      { memory_key: 'fraud_analysis', memory_type: 'working', influence_score: 0.89, content_preview: 'Risk Score: 0.89 - CRITICAL fraud indicators detected' },
    ],
    decision: {
      type: 'FILE SAR',
      confidence: 0.92,
      reasoning: 'Pattern matches historical case SAR-2024-0033. Violates HKMA §35 reporting threshold. Fraud score exceeds critical threshold. Requires immediate compliance review.',
    },
    outputs: [
      { memory_key: 'sar_report', memory_type: 'working', hash: '7f3a9b2c...' }
    ]
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Memory IN */}
      <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Memory IN</h3>
        <p className="text-sm text-gray-600 mb-4">Total Influence Score: 2.53</p>

        <div className="space-y-4">
          {mockTrace.input_influences.map((inf, i) => (
            <div key={i} className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-blue-600">{inf.memory_type}</span>
                <span className="text-sm font-mono text-gray-700">{inf.memory_key}</span>
              </div>

              <p className="text-sm text-gray-600 mb-3 italic">"{inf.content_preview}"</p>

              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all"
                    style={{ width: `${inf.influence_score * 100}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-700 min-w-[3rem]">
                  {inf.influence_score.toFixed(2)}
                </span>
              </div>

              {inf.similarity && (
                <p className="text-xs text-gray-500 mt-2">Similarity: {inf.similarity.toFixed(2)}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Arrow */}
      <div className="flex justify-center">
        <div className="text-5xl text-purple-500">↓</div>
      </div>

      {/* Decision */}
      <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Decision</h3>

        <div className="bg-white rounded-lg p-6 shadow-sm">
          <div className="text-2xl font-bold text-red-600 mb-3">
            {mockTrace.decision.type}
          </div>

          <div className="mb-4">
            <span className="text-sm text-gray-600">Confidence: </span>
            <span className="text-sm font-semibold text-gray-900">
              {(mockTrace.decision.confidence * 100).toFixed(0)}%
            </span>
          </div>

          <div className="border-t border-gray-200 pt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Reasoning:</p>
            <ul className="space-y-2">
              {mockTrace.decision.reasoning.split('. ').filter(s => s).map((sentence, i) => (
                <li key={i} className="flex items-start">
                  <span className="text-purple-500 mr-2">•</span>
                  <span className="text-sm text-gray-700">{sentence}.</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Arrow */}
      <div className="flex justify-center">
        <div className="text-5xl text-purple-500">↓</div>
      </div>

      {/* Memory OUT */}
      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Memory OUT</h3>

        <div className="space-y-3">
          {mockTrace.outputs.map((out, i) => (
            <div key={i} className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-green-600">{out.memory_type}</span>
                <span className="text-sm font-mono text-gray-700">{out.memory_key}</span>
              </div>
              <p className="text-xs text-gray-500 font-mono">Hash: {out.hash}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
