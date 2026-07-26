import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Anxiety Prevalence Predictor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF5642C5)),
        useMaterial3: true,
      ),
      home: const PredictionPage(),
    );
  }
}

class PredictionPage extends StatefulWidget {
  const PredictionPage({super.key});

  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage> {
  final _formKey = GlobalKey<FormState>();

  // API URL — replace with your deployed Render URL
  static const String apiUrl =
      'https://mental-health-anxiety-predictor.onrender.com/predict';

  // Controllers for the 6 model input variables
  final TextEditingController _entityCtrl = TextEditingController();
  final TextEditingController _yearCtrl = TextEditingController();
  final TextEditingController _schizoCtrl = TextEditingController();
  final TextEditingController _depressiveCtrl = TextEditingController();
  final TextEditingController _bipolarCtrl = TextEditingController();
  final TextEditingController _eatingCtrl = TextEditingController();

  String _result = '';
  bool _isLoading = false;

  @override
  void dispose() {
    _entityCtrl.dispose();
    _yearCtrl.dispose();
    _schizoCtrl.dispose();
    _depressiveCtrl.dispose();
    _bipolarCtrl.dispose();
    _eatingCtrl.dispose();
    super.dispose();
  }

  Future<void> _predict() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _result = '';
    });

    try {
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'Entity': int.parse(_entityCtrl.text),
          'Year': int.parse(_yearCtrl.text),
          'Schizophrenia': double.parse(_schizoCtrl.text),
          'Depressive': double.parse(_depressiveCtrl.text),
          'Bipolar': double.parse(_bipolarCtrl.text),
          'Eating': double.parse(_eatingCtrl.text),
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _result =
              'Predicted Anxiety Prevalence: ${data['predicted_anxiety_prevalence']}%';
        });
      } else if (response.statusCode == 422) {
        setState(() {
          _result = 'Error: One or more values are out of range or missing.';
        });
      } else {
        setState(() {
          _result = 'Error: ${response.statusCode} — ${response.body}';
        });
      }
    } catch (e) {
      setState(() {
        _result = 'Error: Could not connect to the API. $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Widget _buildField({
    required String label,
    required String hint,
    required TextEditingController controller,
    required double min,
    required double max,
    bool isInt = false,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: TextFormField(
        controller: controller,
        keyboardType: TextInputType.numberWithOptions(decimal: !isInt),
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          border: const OutlineInputBorder(),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        ),
        validator: (value) {
          if (value == null || value.isEmpty) {
            return '$label is required';
          }
          final parsed = num.tryParse(value);
          if (parsed == null) {
            return isInt ? 'Enter a valid integer' : 'Enter a valid number';
          }
          if (isInt && value.contains('.')) {
            return 'Enter a whole number';
          }
          if (parsed < min || parsed > max) {
            return 'Value must be between $min and $max';
          }
          return null;
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Anxiety Prevalence Predictor'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Card(
                    color: const Color(0xFFEDEAFB),
                    child: const Padding(
                      padding: EdgeInsets.all(12.0),
                      child: Text(
                        'Enter a country code, year, and disorder prevalences '
                        'to predict Anxiety disorder prevalence (share of '
                        'population). Prevalence values are percentages.',
                        style:
                            TextStyle(fontSize: 13, color: Color(0xFF5642C5)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildField(
                    label: 'Country Code (Entity)',
                    hint: '0 to 213 — see country_codes.json',
                    controller: _entityCtrl,
                    min: 0,
                    max: 213,
                    isInt: true,
                  ),
                  _buildField(
                    label: 'Year',
                    hint: '1990 to 2019',
                    controller: _yearCtrl,
                    min: 1990,
                    max: 2019,
                    isInt: true,
                  ),
                  _buildField(
                    label: 'Schizophrenia Prevalence (%)',
                    hint: '0.0 to 1.0',
                    controller: _schizoCtrl,
                    min: 0.0,
                    max: 1.0,
                  ),
                  _buildField(
                    label: 'Depressive Prevalence (%)',
                    hint: '0.0 to 10.0',
                    controller: _depressiveCtrl,
                    min: 0.0,
                    max: 10.0,
                  ),
                  _buildField(
                    label: 'Bipolar Prevalence (%)',
                    hint: '0.0 to 3.0',
                    controller: _bipolarCtrl,
                    min: 0.0,
                    max: 3.0,
                  ),
                  _buildField(
                    label: 'Eating Disorder Prevalence (%)',
                    hint: '0.0 to 3.0',
                    controller: _eatingCtrl,
                    min: 0.0,
                    max: 3.0,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _predict,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF5642C5),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      textStyle: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.bold),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              color: Colors.white,
                              strokeWidth: 2,
                            ),
                          )
                        : const Text('Predict'),
                  ),
                  const SizedBox(height: 20),
                  if (_result.isNotEmpty)
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: _result.startsWith('Error')
                            ? Colors.red.shade50
                            : Colors.green.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: _result.startsWith('Error')
                              ? Colors.red
                              : Colors.green,
                        ),
                      ),
                      child: Text(
                        _result,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: _result.startsWith('Error')
                              ? Colors.red.shade800
                              : Colors.green.shade800,
                        ),
                      ),
                    ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
