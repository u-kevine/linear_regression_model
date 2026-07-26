// Basic smoke test for the Anxiety Prevalence Predictor app.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:student_score_predictor/main.dart';

void main() {
  testWidgets('App loads with Predict button and input fields',
      (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());

    // The Predict button is present.
    expect(find.widgetWithText(ElevatedButton, 'Predict'), findsOneWidget);

    // Six input fields (one per model variable) are present.
    expect(find.byType(TextFormField), findsNWidgets(6));
  });
}
